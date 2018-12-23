from pricegrabber import Grabber
import sys
import logging

if __name__ == '__main__':
    dummy_cfg = {
        'url': sys.argv[1]
    }

    logging.basicConfig(level=logging.DEBUG)

    grabber = Grabber(dummy_cfg)
    print(grabber.grab(save_retrieved_page_at="/tmp/page.html"))
