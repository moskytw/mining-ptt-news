#!/usr/bin/env python


import json
from pathlib import Path

import ptt_core
l = ptt_core.l


_PREPROCESSED_DIR_PATH = Path('preprocessed/')


if not _PREPROCESSED_DIR_PATH.exists():
    _PREPROCESSED_DIR_PATH.mkdir()


def preprocess_to_json_file(html_path):

    l.info('Preprocessing {} ...'.format(html_path))

    json_path = _PREPROCESSED_DIR_PATH / '{}.json'.format(html_path.stem)

    if json_path.exists():
        l.info('Existed and skip {}'.format(json_path))
        return

    # read, parse,

    with html_path.open() as f:

        try:
            parsed_article_d = ptt_core.parse_article_page(f)
        except:
            # around 1.4% hit RuntimeError: the ending text of article may be
            # change. we just ignore them.
            l.info('Exception and skip {}'.format(json_path))
            return

    # and transform

    with json.path.open('w') as f:
        json.dump(parsed_article_d, f)
    l.info('Wrote into {}'.format(json_path))


def preprocess_all(html_dir_path_str):

    for path in Path(html_dir_path_str).glob('*index*'):
        preprocess_to_json_file(path)


if __name__ == '__main__':

    preprocess_all('cache')
