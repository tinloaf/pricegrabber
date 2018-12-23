import os
import re
import json
from .util import Singleton
from .exceptions import ConfigException


class SiteConfig(object):
    '''Holds information how to get prices for one specific website.'''

    def __init__(self, data, name_suggestion=None):
        self._data = data

        self._url_regex = None
        if 'url_regex' in self._data:
            try:
                self._url_regex = re.compile(self._data['url_regex'])
            except re.error as e:
                raise ConfigException("Regular expression {} is invalid: {}".format(
                    self._data['url_regex'], str(e)))

        self._name = name_suggestion
        if 'name' in self._data:
            self._name = self._data['name']

        if 'get_rule' in self._data:
            self._get_rule = self._data['get_rule']
            self._xpath = None
            if 'xpath' in self._data:
                raise ConfigException(
                    "Site config can only have one of 'xpath' or 'get_rule'!")
        else:
            self._get_rule = None
            if 'xpath' not in self._data:
                raise ConfigException(
                    "Site config has neither an 'xpath' nor an 'get_rule' entry.")

            self._xpath = self._data['xpath']

        self._value_getters = None
        if 'value_getters' in self._data:
            self._value_getters = []
            for vg_data in self._data['value_getters']:
                if not 'regexp' in vg_data:
                    raise ConfigException("Value getter has no regexp.")
                vg_re_str = vg_data['regexp']

                if not 'function' in vg_data:
                    raise ConfigException("Value getter has no function.")
                vg_func_str = vg_data['function']

                try:
                    value_getter_func = eval(vg_func_str)
                except Exception as e:
                    raise ConfigException(
                        "Value getter function specification '{}' is not valid Python code: {}".format(vg_func_str, str(e)))

                try:
                    self._value_getters.append(
                        (re.compile(vg_re_str), value_getter_func)
                    )
                except re.error:
                    raise ConfigException("Regular expression {} is invalid: {}".format(
                        vg_re_str, str(e)))

        self._currency_getters = None
        if 'currency_getters' in self._data:
            self._currency_getters = []
            for cg_data in self._data['currency_getters']:
                if 'regexp' not in cg_data:
                    raise ConfigException('Currency getter has no regexp.')
                search_re_str = cg_data['regexp']

                if 'symbol' not in cg_data:
                    raise ConfigException('Currency getter has no symbol.')
                symbol = cg_data['symbol']

                try:
                    self._currency_getters.append(
                        (re.compile(search_re_str), symbol))
                except re.error as e:
                    raise ConfigException(
                        "Regular experession {} is invalid: {}".format(search_re_str, str(e)))

        self._fixed_currency = None
        if 'fixed_currency' in self._data:
            self._fixed_currency = self._data['fixed_currency']

        self._tests = self._data.get("tests", [])

    def get_url_regex(self):
        return self._url_regex

    def get_name(self):
        return self._name

    def get_xpath(self):
        return self._xpath

    def get_get_rule(self):
        return self._get_rule

    def get_value_getters(self):
        return self._value_getters

    def get_currency_getters(self):
        return self._currency_getters

    def get_fixed_currency(self):
        return self._fixed_currency


class SiteConfigRepo(object, metaclass=Singleton):
    '''Singleton class holding all available SiteConfigs'''

    def __init__(self, **kwargs):
        if 'data_dir' in kwargs:
            self._initialize(kwargs['data_dir'])

    def _initialize(self, data_dir):
        self._site_configs = []

        for root, dirs, files in os.walk(data_dir):
            for filename in files:
                full_name = os.path.join(root, filename)
                if full_name[-5:] == '.json':
                    name_suggestion = full_name[:5]
                    with open(full_name, 'r') as input_file:
                        json_data = json.load(input_file)
                        for entry in json_data:
                            self._site_configs.append(SiteConfig(
                                entry, name_suggestion=name_suggestion))

    def get_configs(self):
        return self._site_configs
