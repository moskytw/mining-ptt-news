#!/usr/bin/env python


import json
from os import scandir
from os.path import (
    join as path_join,
    basename as to_basename,
    splitext,
    exists
)

import ptt_core
l = ptt_core.l


_PREPROCESSED_DIR_PATH = 'preprocessed'


def preprocess_to_json_file(html_path):

    l.info('Preprocessing {} ...'.format(html_path))

    basename = to_basename(html_path)
    root, ext = splitext(basename)
    json_path = path_join(_PREPROCESSED_DIR_PATH, '{}.json'.format(root))

    if exists(json_path):
        l.info('Existed and skip {}'.format(json_path))
        return

    # read, parse,

    with open(html_path) as f:

        try:
            parsed_article_d = ptt_core.parse_article_page(f)
        except:
            # around 1.4% hit RuntimeError: the ending text of article may be
            # change. we just ignore them.
            l.info('Exception and skip {}'.format(json_path))
            return

    # and transform

    with ptt_core.mkdir_n_open(json_path, 'w') as f:
        json.dump(parsed_article_d, f)
    l.info('Wrote into {}'.format(json_path))


def preprocess_all(html_dir_path):

    for dir_entry in scandir(html_dir_path):

        path = dir_entry.path

        if 'index' in path:
            continue

        preprocess_to_json_file(dir_entry.path)


if __name__ == '__main__':

    preprocess_all('cache')
