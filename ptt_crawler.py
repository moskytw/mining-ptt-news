#!/usr/bin/env python


from os import mkdir
from os.path import join as path_join
from urllib.parse import quote_plus
from time import sleep
from random import randint

import requests

import ptt
l = ptt.l


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


_SHARED_FAKE_BROWSER = _make_fake_browser()
_CACHE_DIR_PATH = 'cache/'
_URL_SET_SKIPPING_CACHE = {'https://www.ptt.cc/bbs/Gossiping/index.html'}


def read_or_request(url):

    # should generate valid fname for most of the systems
    fname = quote_plus(url)
    path = path_join(_CACHE_DIR_PATH, fname)

    # try cache

    if url in _URL_SET_SKIPPING_CACHE:

        l.info('Skip cache for {}'.format(url))

    else:

        try:
            with open(path) as f:
                l.info('Hit {}'.format(url))
                return f.read()
        except OSError:
            l.info('Missed {}'.format(url))

    # request

    resp = _SHARED_FAKE_BROWSER.get(url)
    text = resp.text

    while 1:

        try:
            with open(path, 'w') as f:
                f.write(text)
        except FileNotFoundError:
            mkdir(_CACHE_DIR_PATH)
            continue
        else:
            l.info('Wrote {}'.format(url))

        # only loop once normally
        break

    return text


def crawl(index_url):

    count = 0
    prev_url = index_url

    while 1:

        # crawl and parse the index page

        l.info('Crawl the index page {} ...'.format(prev_url))
        try:
            text = read_or_request(prev_url)
        except OSError:
            # try again
            l.info('Try again ...')
            text = read_or_request(prev_url)

        l.info('Parse the index page {} ...'.format(prev_url))
        parsed_index_d = ptt.parse_index_page(text)

        prev_url = parsed_index_d['prev_url']

        # crawl the article_url

        for entry_d in parsed_index_d['entry_ds']:

            article_url = entry_d['article_url']
            # if deleted article
            if not article_url:
                continue

            # skip non-news
            if not entry_d['title'].startswith('[新聞]'):
                continue

            l.info('Crawl the article page {} ...'.format(article_url))
            try:
                read_or_request(article_url)
            except OSError:
                # try again
                l.info('Try again ...')
                try:
                    read_or_request(article_url)
                except OSError:
                    # skip if still fail
                    l.info('Skip')
                    continue

            count += 1

            l.info('Sleep')
            sleep(randint(0, 10)*0.001)

        l.info('Got {:,} articles so far'.format(count))


if __name__ == '__main__':

    from pprint import pprint

    #crawl('https://www.ptt.cc/bbs/Gossiping/index.html')

    import sys
    sys.exit()

    pprint(ptt.parse_article_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/M.1480355255.A.07C.html'
    )))

    import sys
    sys.exit()

    # test the index page
    pprint(ptt.parse_index_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/index20177.html'
    )))

    # test the article page #1
    pprint(ptt.parse_article_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/M.1480367106.A.A55.html'
    )))

    # test the article page #2
    pprint(ptt.parse_article_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/M.1480380251.A.9A4.html'
    )))
