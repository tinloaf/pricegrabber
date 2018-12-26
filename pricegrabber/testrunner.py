"""Run tests against live websites."""

from .grabber import Grabber
from .siteconfig import SiteConfigRepo


class TestRunner(object):
    """Runs tests against live websites."""

    def __init__(self):
        self._failed_info = []

    def run_all(self):
        """Run all configured tests."""
        config_repo = SiteConfigRepo()
        failed_infos = []
        for site_config in config_repo.get_configs():
            failed_infos.extend(self._run_one(site_config))

        if failed_infos:
            print("========= {} ERRORS ===========".format(len(failed_infos)))

        for fail in failed_infos:
            print("--------------------------------------------------------")
            print("Failed Config: {}".format(fail['config']))
            print("Failed URL: {}".format(fail['url']))
            print("Kind of expectation: {}".format(fail['expectation']))
            print("Expected value: {}".format(fail['expected']))
            print("Value seen: {}".format(fail['seen']))

    def _check_number_of_prices(self, test, prices, scfg):
        if 'number-of-prices' in test:
            if len(prices) != test['number-of-prices']:
                self._failed_info.append(
                    {'config': scfg.get_name(),
                     'url': test["url"],
                     'expectation': 'number-of-prices',
                     'expected': test['number-of-prices'],
                     'seen': len(prices)})
                return False
        return True

    def _check_price_range(self, test, prices, scfg):
        success = True

        if 'price-min' in test:
            for price, _ in prices:
                if price < test['price-min']:
                    self._failed_info.append(
                        {'config': scfg.get_name(),
                         'url': test["url"],
                         'expectation': 'price-min',
                         'expected': test['price-min'],
                         'seen': price})
                    success = False

        if 'price-max' in test:
            for price, _ in prices:
                if price > test['price-max']:
                    self._failed_info.append(
                        {'config': scfg.get_name(),
                         'url': test["url"],
                         'expectation': 'price-max',
                         'expected': test['price-max'],
                         'seen': price})
                    success = False

        return success

    def _check_currency(self, test, prices, scfg):
        if 'currency' in test:
            for _, currency in prices:
                if currency != test['currency']:
                    self._failed_info.append(
                        {'config': scfg.get_name(),
                         'url': test["url"],
                         'expectation': 'currency',
                         'expected': test['currency'],
                         'seen': currency})
                    return False
        return True

    def _run_one(self, scfg):
        self._failed_info = []

        print("Testing {}: ".format(scfg.get_name()), end='')

        for test in scfg.get_tests():
            url = test["url"]

            grabber = Grabber({"url": url,
                               "site_config": scfg})

            prices = grabber.grab()

            success = True

            success &= self._check_number_of_prices(test, prices, scfg)
            success &= self._check_price_range(test, prices, scfg)
            success &= self._check_currency(test, prices, scfg)

            if not success:
                print("X", end='')
            else:
                print(".", end='')

        print(" Done")
        return self._failed_info
