#!/usr/bin/env python


from pprint import pprint
import logging
from bs4 import BeautifulSoup
import requests


logging.basicConfig(
    format=(
        '%(asctime)s\t%(levelname)s\t'
        #'%(processName)s\t%(threadName)s\t'
        '%(name)s\t%(funcName)s:%(lineno)d\t'
        '%(message)s'
    ),
    level=logging.DEBUG
)


def make_fake_browser():

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


def save_index_html():

    fake_browser = make_fake_browser()
    resp = fake_browser.get('https://www.ptt.cc/bbs/Gossiping/index.html')

    with open('index.html', 'w') as f:
        f.write(resp.text)

    logging.info('Saved index.html')


if __name__ == '__main__':

    save_index_html()
