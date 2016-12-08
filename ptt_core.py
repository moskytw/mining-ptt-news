#!/usr/bin/env python


import logging
from urllib.parse import urljoin
from datetime import datetime

from bs4 import BeautifulSoup


logging.basicConfig(
    format=(
        '%(asctime)s\t%(levelname)s\t'
        #'%(processName)s\t%(threadName)s\t'
        '%(module)s\t%(funcName)s:%(lineno)d\t'
        '%(message)s'
    ),
    level=logging.DEBUG
)
l = logging.getLogger('ptt')


_ROOT_URL = 'https://www.ptt.cc'


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

    prev_href = prev_a_tag.get('href', '')
    prev_url = prev_href and urljoin(_ROOT_URL, prev_href)
    next_href = next_a_tag.get('href', '')
    next_url = next_href and urljoin(_ROOT_URL, next_href)

    # entries

    entry_ds = []
    ent_tags = soup.select('.r-list-container .r-ent')
    for ent_tag in ent_tags:

        # push_score_sum

        # cases
        #
        # 1. <div class="nrec"><span class="hl f3">12</span></div>
        # 2. <div class="nrec"></div>
        # 3. <div class="nrec"><span class="hl f0">X1</span></div>
        #

        push_score_sum = -65535
        span_tag = ent_tag.find(class_='nrec').find('span')

        # if case 2
        if not span_tag:

            push_score_sum = 0

        else:

            span_text = span_tag.string

            while 1:

                # if case 1
                try:
                    push_score_sum = int(span_text)
                except ValueError:
                    pass
                else:
                    break

                # if case 3
                try:
                    push_score_sum = int(span_text[1:])
                except ValueError:
                    pass
                else:
                    # TODO: is it correct?
                    push_score_sum = -(push_score_sum+10)
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

        title_tag = ent_tag.find(class_='title')
        title_a_tag = title_tag.a
        if title_a_tag:
            # case 1
            # the case in https://www.ptt.cc/bbs/Gossiping/index19183.html
            title = title_a_tag.string or ''
            article_url = urljoin(_ROOT_URL, title_a_tag.get('href', ''))
        else:
            # case 2: deleted article
            title = title_tag.string.strip()
            article_url = ''

        # others

        ent_meta_tag = ent_tag.find(class_='meta')

        # mmdd won't contain year!
        raw_mmdd = ent_meta_tag.find(class_='date').string
        author_id = ent_meta_tag.find(class_='author').string
        # deleted article
        if not article_url and author_id == '-':
            author_id = ''

        # append

        entry_ds.append({
            'push_score_sum' : push_score_sum,
            'title'          : title,
            'article_url'    : article_url,
            'raw_mmdd'       : raw_mmdd,
            'author_id'      : author_id
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
    authored_ts = (
        datetime
        .strptime(timestamp_text, '%a %b %d %H:%M:%S %Y')
        .timestamp()
    )

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

        raise RuntimeError('the ending text of article may be change')

    # ... 以後台北人都要去高雄當台勞了。\n\n--'
    body = '\n'.join(body_lines).rstrip('\n-')

    # pushes

    push_ds = [
        {
            'score': _PUSH_TAG_STRIPPED_TEXT_SCORE_MAP.get(
                push_tag.find(class_='push-tag').string.strip(), -255
            ),
            'pusher_id': push_tag.find(class_='push-userid').string,
            # consider topractise's push in
            # https://www.ptt.cc/bbs/Gossiping/M.1480355255.A.07C.html
            'text': push_tag.find(class_='push-content').string or '',
            # won't contain year!
            'raw_mmddhhmm': (
                push_tag.find(class_='push-ipdatetime').string.strip()
            )
        }
        for push_tag in main_content_tag.select('.push')
    ]

    return {
        'board_name' : board_name,
        'author_id'  : author_id,
        'author_nick': author_nick,
        'title'      : title,
        'authored_ts': authored_ts,
        'body'       : body,
        'push_ds'    : push_ds
    }


if __name__ == '__main__':

    from pprint import pprint

    with open(
        'cache/'
        'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FGossiping%2FM.1480162206.A.433.html'
    ) as f:
        pprint(parse_article_page(f))
