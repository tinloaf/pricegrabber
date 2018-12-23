from pricegrabber import TestRunner
import sys
import logging


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    tr = TestRunner()
    tr.run_all()
