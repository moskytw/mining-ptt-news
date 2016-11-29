#!/usr/bin/env python


from os import mkdir
from os.path import join as path_join
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


_SHARED_FAKE_BROWSER = _make_fake_browser()
_CACHE_DIR_PATH = 'cache/'


def read_or_request(url):

    # should generate valid fname for most of the systems
    fname = quote_plus(url)
    path = path_join(_CACHE_DIR_PATH, fname)

    # try cache

    try:
        with open(path) as f:
            logging.info('Hit {}'.format(url))
            return f.read()
    except OSError:
        logging.info('Missed {}'.format(url))

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
            logging.info('Wrote {}'.format(url))

        # only loop once normally
        break

    return text


_ROOT = 'https://www.ptt.cc'


def parse_index_page(text):

    soup = BeautifulSoup(text, 'html.parser')

    # paging

    paging_a_tags = soup.select('.action-bar .btn-group-paging a')

    prev_a_tag = paging_a_tags[1]
    next_a_tag = paging_a_tags[2]

    if '上頁' not in prev_a_tag.string:
        raise RuntimeError('the prev button looks not right')
    if '下頁' not in next_a_tag.string:
        raise RuntimeError('the next button looks not right')

    prev_url = path_join(_ROOT, prev_a_tag.get('href', ''))
    next_url = path_join(_ROOT, next_a_tag.get('href', ''))

    # entries

    entry_ds = []
    ent_tags = soup.select('.r-list-container .r-ent')
    for ent_tag in ent_tags:

        # push_count

        # cases
        #
        # 1. <div class="nrec"><span class="hl f3">12</span></div>
        # 2. <div class="nrec"></div>
        # 3. <div class="nrec"><span class="hl f0">X1</span></div>
        #
        push_count = -65535
        span_tags = ent_tag.select('.nrec span')

        # if case 2
        if not span_tags:

            push_count = 0

        else:

            span_text = span_tags[0].string

            while 1:

                # if case 1
                try:
                    push_count = int(span_text)
                except ValueError:
                    pass
                else:
                    break

                # if case 3
                try:
                    push_count = int(span_text[1:])
                except ValueError:
                    pass
                else:
                    push_count = -(push_count+10)
                    break

                # loop once normally
                break

        # title & enrty_url

        # cases
        #
        # 1. <div class="title">
        #        <a href="/bbs/Gossiping/M.1480367106.A.A55.html">
        #            Re: [問卦] 有沒有高雄其實比台北進步的八卦??
        #        </a>
        #    </div>
        # 2. <div class="title"> (本文已被刪除) [gundam0613] </div>
        #

        title_a_tag = ent_tag.find(class_='title').a
        title = title_a_tag.string

        title_href = title_a_tag.get('href', '')
        if title_href:
            article_url = path_join(_ROOT, title_href)
        else:
            article_url = ''

        # others

        ent_meta_tag = ent_tag.find(class_='meta')

        # mmdd won't contain year!
        mmdd = '{:0>2}{:0>2}'.format(
            *ent_meta_tag.find(class_='date').string.split('/')
        )
        author_id = ent_meta_tag.find(class_='author').string

        # append

        entry_ds.append({
            'push_count' : push_count,
            'title'      : title,
            'article_url': article_url,
            'mmdd'       : mmdd,
            'author_id'  : author_id
        })

    return {
        'prev_url': prev_url,
        'next_url': next_url,
        'entry_ds': entry_ds
    }


if __name__ == '__main__':

    from pprint import pprint

    pprint(parse_index_page(
        read_or_request('https://www.ptt.cc/bbs/Gossiping/index.html')
    ))
