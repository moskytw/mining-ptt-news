#!/usr/bin/env python


import logging
from os import mkdir
from os.path import join as path_join
from urllib.parse import quote_plus, urljoin
from datetime import datetime

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
_URL_SET_SKIPPING_CACHE = {'https://www.ptt.cc/bbs/Gossiping/index.html'}


def read_or_request(url):

    # should generate valid fname for most of the systems
    fname = quote_plus(url)
    path = path_join(_CACHE_DIR_PATH, fname)

    # try cache

    if url in _URL_SET_SKIPPING_CACHE:

        logging.info('Skip cache for {}'.format(url))

    else:

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

    prev_url = urljoin(_ROOT, prev_a_tag.get('href', ''))
    next_url = urljoin(_ROOT, next_a_tag.get('href', ''))

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
        span_tag = ent_tag.find(class_='nrec').find('span')

        # if case 2
        if not span_tag:

            push_count = 0

        else:

            span_text = span_tag.string

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
                    # TODO: is it correct?
                    push_count = -(push_count+10)
                    break

                # loop once normally
                break

        # title & article_url

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
        if not title_a_tag:
            continue

        title = title_a_tag.string
        article_url = urljoin(_ROOT, title_a_tag.get('href', ''))

        # others

        ent_meta_tag = ent_tag.find(class_='meta')

        # mmdd won't contain year!
        raw_mmdd = ent_meta_tag.find(class_='date').string
        author_id = ent_meta_tag.find(class_='author').string

        # append

        entry_ds.append({
            'push_count' : push_count,
            'title'      : title,
            'article_url': article_url,
            'raw_mmdd'   : raw_mmdd,
            'author_id'  : author_id
        })

    return {
        'prev_url': prev_url,
        'next_url': next_url,
        'entry_ds': entry_ds
    }


_EXPECTED_ARTICLE_TAG_KEYS = ('作者', '看板', '標題', '時間')
_PUSH_TAG_STRIPPED_TEXT_SCORE_MAP = {
    '噓': -1,
    '→': 0,
    '推': 1
}


def parse_article_page(text):

    soup = BeautifulSoup(text, 'html.parser')
    main_content_tag = soup.find(id='main-content')

    # meta
    #
    # <div class="article-metaline">
    #     <span class="article-meta-tag">作者</span>
    #     <span class="article-meta-value">a77774444 (我愛ˋ台灣)</span>
    # </div>
    #
    for tag, key in zip(
        main_content_tag.select('.article-meta-tag'),
        _EXPECTED_ARTICLE_TAG_KEYS
    ):
        if tag.string != key:
            raise RuntimeError('the article tags may be changed')

    author_line, board_name, title, timestamp_text = (
        tag.string
        for tag in main_content_tag.select('.article-meta-value')
    )

    author_id, _, author_line_tail = author_line.partition(' (')
    author_nick = author_line_tail[:-1]

    # Tue Nov 29 05:05:03 2016
    # Fri Jul  1 21:12:25 2005
    created_dt = datetime.strptime(timestamp_text, '%a %b %d %H:%M:%S %Y')

    # body

    recording = False
    body_lines = []
    for i, line in enumerate(main_content_tag.stripped_strings):

        if i == 6:
            if line != '時間':
                raise RuntimeError('the article structure may be changed')
        elif i == 8:
            recording = True
        elif line.startswith('※ 發信站: 批踢踢實業坊'):
            recording = False
            break

        if recording:
            body_lines.append(line)

    else:

        raise RuntimeError('the ending text of article may be change/')

    # ... 以後台北人都要去高雄當台勞了。\n\n--'
    body = '\n'.join(body_lines).rstrip('\n-')

    # pushes

    push_ds = [
        {
            'score': _PUSH_TAG_STRIPPED_TEXT_SCORE_MAP.get(
                push_tag.find(class_='push-tag').string.strip(), -255
            ),
            'id': push_tag.find(class_='push-userid').string,
            'text': push_tag.find(class_='push-content').string,
            # won't contain year!
            'raw_mmddhhmm': push_tag.find(class_='push-ipdatetime').string.strip()
        }
        for push_tag in main_content_tag.select('.push')
    ]

    return {
        'board_name' : board_name,
        'author_id'  : author_id,
        'author_nick': author_nick,
        'title'      : title,
        'created_dt' : created_dt,
        'body'       : body,
        'push_ds'    : push_ds
    }


if __name__ == '__main__':

    from pprint import pprint

    # test the index page
    pprint(parse_index_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/index20177.html'
    )))

    # test the article page #1
    pprint(parse_article_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/M.1480367106.A.A55.html'
    )))

    # test the article page #2
    pprint(parse_article_page(read_or_request(
        'https://www.ptt.cc/bbs/Gossiping/M.1480380251.A.9A4.html'
    )))
