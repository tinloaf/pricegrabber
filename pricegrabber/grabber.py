"""The Grabber is the main class to scrape prices."""

import logging
import re
import requests
from lxml import html

from .siteconfig import SiteConfigRepo
from .exceptions import NetworkException, ConfigException

LOGGER = logging.getLogger(__name__)
ELEMENTS_LOGGER = logging.getLogger(__name__ + '.elements')


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

        You must supply a `config` dictionary. This dictionary *must*
        contain the key 'url'. From that URL, the Grabber will try to
        scrape prices."""

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
            page_content = requests.get(self._cfg['url'],
                                        headers={"User-Agent": "PriGra v.0.0.1"})
            redirected_url = page_content.url
        except Exception:
            LOGGER.error("Could not fetch {} to determine site configs!")

        config_repo = SiteConfigRepo()
        for site_config in config_repo.get_configs():
            if site_config.get_name() and site_config.get_name() in self._cfg.get('exclude', ()):
                continue

            url_regex = site_config.get_url_regex()
            if not url_regex:
                self._site_configs.append(site_config)
            else:
                match = url_regex.match(self._cfg['url'])
                if match:
                    self._site_configs.append(site_config)
                else:
                    match = url_regex.match(redirected_url)
                    if match:
                        self._site_configs.append(site_config)

    def _get_price(self, text, site_config):
        LOGGER.debug(" --> Parsing price from '%s'", text)
        value_getters = Grabber.DEFAULT_VALUE_GETTERS
        if site_config.get_value_getters():
            value_getters = site_config.get_value_getters()

        longest_converted_val = None
        longest_converted_length = 0
        for (value_re, value_func) in value_getters:
            ELEMENTS_LOGGER.debug(" ---> Trying %s", value_re.pattern)
            match = value_re.search(text)
            if not match:
                ELEMENTS_LOGGER.debug(" ----> No Match.")
                continue
            try:
                ELEMENTS_LOGGER.debug(
                    " ----> Success. Match group: %s", match.group(0))
                if len(match.group(0)) > longest_converted_length:
                    longest_converted_val = value_func(match.group(0))
                    longest_converted_length = len(match.group(0))
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
            match = currency_re.search(text)
            if match:
                return currency_symbol

        return None

    def _get_by_xpath(self, tree, scfg):
        potential_prices = []
        ELEMENTS_LOGGER.debug("Getting by XPath '%s'", scfg.get_xpath())

        elements = tree.xpath(scfg.get_xpath())
        ELEMENTS_LOGGER.debug(
            " -> XPath produced %s elements", len(elements))
        for element in elements:
            price = self._get_price(element.text_content(), scfg)
            if price:
                currency = self._get_currency(element.text_content(), scfg)
                potential_prices.append((price, currency))

        return potential_prices

    def _get_elements_by_xpath(self, tree, rule):
        xpath = rule.get('xpath')

        ELEMENTS_LOGGER.debug("Getting elements by XPath '%s'", xpath)

        if not xpath:
            raise ConfigException(
                "XPath get-rule has no 'xpath'.")
        return tree.xpath(xpath)

    def _get_elements_by_fallthrough(self, tree, rule):
        ELEMENTS_LOGGER.debug("Getting by fallthrough")

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
        for element in elements:
            price = self._get_price(element.text_content(), scfg)
            if price:
                currency = self._get_currency(element.text_content(), scfg)
                potential_prices.append((price, currency))

        return potential_prices

    def grab(self, save_retrieved_page_at=None):
        """Scrape and return prices.

        Returns a list of all found prices. Every item in the list is a
        pair of price and currency.

        If you set the optional `save_retrieved_page_at`, the page accessed
        (last) during the grab will be saved to the respective location.
        Use this only for debugging purposes.
        """

        try:
            page_content = requests.get(self._cfg['url'], headers={
                "User-Agent": "PriGra v.0.0.1"})
            page_content.raise_for_status()

            if save_retrieved_page_at:
                with open(save_retrieved_page_at, "w") as page_output_file:
                    page_output_file.write(
                        page_content.content.decode('utf-8'))
        except requests.exceptions.ConnectionError as exc:
            raise NetworkException("Connection Error: {}".format(str(exc)))
        except requests.exceptions.HTTPError as exc:
            raise NetworkException("HTTP Error: {}".format(str(exc)))
        except requests.exceptions.Timeout as exc:
            raise NetworkException("Network Timeout: {}".format(str(exc)))

        tree = html.fromstring(page_content.content)

        potential_prices = []

        for scfg in self._site_configs:
            if scfg.get_xpath():
                potential_prices.extend(self._get_by_xpath(tree, scfg))
            else:
                potential_prices.extend(self._get_by_rule(tree, scfg))

        return potential_prices
