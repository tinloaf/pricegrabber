from .grabber import Grabber
from .siteconfig import SiteConfigRepo


class TestRunner(object):
    def __init__(self):
        pass

    def run_all(self):
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

    def _run_one(self, scfg):
        failed_info = []

        print("Testing {}: ".format(scfg._name), end='')

        for test in scfg._tests:
            url = test["url"]

            g = Grabber({"url": url,
                         "site_config": scfg})

            prices = g.grab()

            failed = False

            if 'number-of-prices' in test:
                if len(prices) != test['number-of-prices']:
                    failed_info.append(
                        {'config': scfg._name,
                         'url': test["url"],
                         'expectation': 'number-of-prices',
                         'expected': test['number-of-prices'],
                         'seen': len(prices)})
                    failed = True

            if 'price-min' in test:
                for price, _ in prices:
                    if price < test['price-min']:
                        failed_info.append(
                            {'config': scfg._name,
                             'url': test["url"],
                             'expectation': 'price-min',
                             'expected': test['price-min'],
                             'seen': price})
                        failed = True

            if 'price-max' in test:
                for price, _ in prices:
                    if price > test['price-max']:
                        failed_info.append(
                            {'config': scfg._name,
                             'url': test["url"],
                             'expectation': 'price-max',
                             'expected': test['price-max'],
                             'seen': price})
                        failed = True

            if 'currency' in test:
                for _, currency in prices:
                    if currency != test['currency']:
                        failed_info.append(
                            {'config': scfg._name,
                             'url': test["url"],
                             'expectation': 'currency',
                             'expected': test['currency'],
                             'seen': currency})
                        failed = True

            if failed:
                print("X", end='')
            else:
                print(".", end='')

        print(" Done")
        return failed_info
