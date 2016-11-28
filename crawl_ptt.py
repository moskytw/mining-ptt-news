#!/usr/bin/env python


from os import mkdir
from urllib.parse import quote_plus
import logging

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    format=(
        '%(asctime)s\t%(levelname)s\t'
        #'%(processName)s\t%(threadName)s\t'
        '%(name)s\t%(funcName)s:%(lineno)d\t'
        '%(message)s'
    ),
    level=logging.DEBUG
)


def _make_fake_browser():

    fake_browser = requests.Session()
    fake_browser.headers = {
        'user-agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/54.0.2840.98 Safari/537.36'
        ),
        'accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/webp,*/*;q=0.8'
        ),
        'accept-encoding': 'gzip, deflate, sdch, br',
        'accept-language': 'en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4',
        'cookie': 'over18=1',
    }

    return fake_browser


_shared_fake_browser = _make_fake_browser()
_CACHE_DIR_PATH = 'cache/'


def read_or_request(url):

    # should generate valid fname for most of the systems
    fname = quote_plus(url)
    path = '{}{}'.format(_CACHE_DIR_PATH, fname)

    # try cache

    try:
        with open(path) as f:
            logging.info('Hit {}'.format(url))
            return f.read()
    except OSError:
        logging.info('Missed {}'.format(url))

    # request

    resp = _shared_fake_browser.get(url)
    text = resp.text

    while 1:

        try:
            with open(path, 'w') as f:
                f.write(text)
        except FileNotFoundError:
            mkdir(_CACHE_DIR_PATH)
            continue
        else:
            logging.info('Wrote {}'.format(url))
            break

    return text


if __name__ == '__main__':

    read_or_request('https://www.ptt.cc/bbs/Gossiping/index.html')
