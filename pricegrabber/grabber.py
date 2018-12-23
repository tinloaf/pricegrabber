from .siteconfig import SiteConfigRepo
from .exceptions import NetworkException, ConfigException

import logging
import requests
from lxml import html
import re

logger = logging.getLogger(__name__)
elements_logger = logging.getLogger(__name__ + '.elements')


def _make_simple_currency_getters(currencies):
    return [(re.compile(match_str), symbol) for (match_str, symbol) in currencies]


class Grabber(object):
    """Object that scrapes prices from various websites."""
    DEFAULT_VALUE_GETTERS = (
        (re.compile(r'\d+(\.\d{3})*(,\d{1,2})?'),
         lambda value_str: float(value_str.replace('.', '').replace(',', '.'))),
        (re.compile(r'\d+(,\d{3})*(.\d{1,2})?'),
         lambda value_str: float(value_str.replace(',', '')))
    )
    DEFAULT_CURRENCY_GETTERS = _make_simple_currency_getters((
        ('€', '€'), ('EUR', '€'), ('PLN',
                                   'zł'), ('zł', 'zł'), ('GBP', '£'), ('£', '£'),
        ('USD', '$'), (r'\$', '$')
    ))

    def __init__(self, config):
        """Create a new Grabber.

        You must supply a `config` dictionary. This dictionary *must* contain the key 'url'. From that URL, the Grabber will try to scrape prices."""

        self._cfg = config

        self._site_configs = []
        self._init_site_configs()

    def _init_site_configs(self):
        # Identify which site configs are candidates
        self._site_configs = []

        if "site_config" in self._cfg:
            # Site config is forced!
            self._site_configs = [self._cfg["site_config"]]
            return

        # Resolve the URL once to figure out redirects
        redirected_url = None
        try:
            page_content = requests.get(self._cfg['url'], headers={
                                        "User-Agent": "PriGra v.0.0.1"})
            redirected_url = page_content.url
        except:
            logger.error("Could not fetch {} to determine site configs!")

        config_repo = SiteConfigRepo()
        for site_config in config_repo.get_configs():
            if site_config.get_name() and site_config.get_name() in self._cfg.get('exclude', ()):
                continue

            url_regex = site_config.get_url_regex()
            if not url_regex:
                self._site_configs.append(site_config)
            else:
                m = url_regex.match(self._cfg['url'])
                if m:
                    self._site_configs.append(site_config)
                else:
                    m = url_regex.match(redirected_url)
                    if m:
                        self._site_configs.append(site_config)

    def _get_price(self, text, site_config):
        logger.debug(" --> Parsing price from '{}'".format(text))
        value_getters = Grabber.DEFAULT_VALUE_GETTERS
        if site_config.get_value_getters():
            value_getters = site_config.get_value_getters()

        longest_converted_val = None
        longest_converted_length = 0
        for (value_re, value_func) in value_getters:
            elements_logger.debug(" ---> Trying {}".format(value_re.pattern))
            m = value_re.search(text)
            if not m:
                elements_logger.debug(" ----> No Match.")
                continue
            try:
                elements_logger.debug(
                    " ----> Success. Match group: {}".format(m.group(0)))
                if len(m.group(0)) > longest_converted_length:
                    longest_converted_val = value_func(m.group(0))
                    longest_converted_length = len(m.group(0))
            except ValueError:
                pass

        return longest_converted_val

    def _get_currency(self, text, site_config):
        if site_config.get_fixed_currency():
            return site_config.get_fixed_currency()

        currency_getters = Grabber.DEFAULT_CURRENCY_GETTERS
        if site_config.get_currency_getters():
            currency_getters = site_config.get_currency_getters()

        for (currency_re, currency_symbol) in currency_getters:
            m = currency_re.search(text)
            if m:
                return currency_symbol

        return None

    def _get_by_xpath(self, tree, scfg):
        potential_prices = []
        elements_logger.debug("Getting by XPath {}".format(scfg.get_xpath()))

        elements = tree.xpath(scfg.get_xpath())
        elements_logger.debug(
            " -> XPath produced {} elements".format(len(elements)))
        for el in elements:
            price = self._get_price(el.text_content(), scfg)
            if price:
                currency = self._get_currency(el.text_content(), scfg)
                potential_prices.append((price, currency))

        return potential_prices

    def _get_elements_by_xpath(self, tree, rule):
        xpath = rule.get('xpath')

        elements_logger.debug("Getting elements by XPath {}".format(xpath))

        if not xpath:
            raise ConfigException(
                "XPath get-rule has no 'xpath'.")
        return tree.xpath(xpath)

    def _get_elements_by_fallthrough(self, tree, rule):
        elements_logger.debug("Getting by fallthrough")

        children = rule.get('children', [])
        for child in children:
            elements = self._get_elements_by_rule(tree, child)
            if elements:
                return elements

        return []

    def _get_elements_by_rule(self, tree, rule):
        rtype = rule.get('type')
        if not rtype:
            raise ConfigException(
                "Get-rule has no 'type'.")

        if rtype == 'xpath':
            return self._get_elements_by_xpath(tree, rule)
        elif rtype == 'fallthrough':
            return self._get_elements_by_fallthrough(tree, rule)
        else:
            raise ConfigException(
                "Unknown get-rule type {}.".format(rule['type']))

    def _get_by_rule(self, tree, scfg):
        rule = scfg.get_get_rule()

        elements = self._get_elements_by_rule(tree, rule)

        potential_prices = []
        for el in elements:
            price = self._get_price(el.text_content(), scfg)
            if price:
                currency = self._get_currency(el.text_content(), scfg)
                potential_prices.append((price, currency))

        return potential_prices

    def grab(self, save_retrieved_page_at=None):
        """Scrape and return prices.

        Returns a list of all found prices. Every item in the list is a pair of price and currency.

        If you set the optional `save_retrieved_page_at`, the page accessed (last) during the grab will be saved to the respective location. Use this only for debugging purposes.
        """

        try:
            page_content = requests.get(self._cfg['url'], headers={
                "User-Agent": "PriGra v.0.0.1"})
            page_content.raise_for_status()

            if save_retrieved_page_at:
                with open(save_retrieved_page_at, "w") as page_output_file:
                    page_output_file.write(
                        page_content.content.decode('utf-8'))
        except requests.exceptions.ConnectionError as e:
            raise NetworkException("Connection Error: {}".format(str(e)))
        except requests.exceptions.HTTPError as e:
            raise NetworkException("HTTP Error: {}".format(str(e)))
        except requests.exceptions.Timeout as e:
            raise NetworkException("Network Timeout: {}".format(str(e)))

        tree = html.fromstring(page_content.content)

        potential_prices = []

        for scfg in self._site_configs:
            if scfg.get_xpath():
                potential_prices.extend(self._get_by_xpath(tree, scfg))
            else:
                potential_prices.extend(self._get_by_rule(tree, scfg))

        return potential_prices
