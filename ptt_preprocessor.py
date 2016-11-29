#!/usr/bin/env python


import json
from os import mkdir, scandir
from os.path import (
    join as path_join,
    basename as to_basename,
    splitext,
    exists
)

import ptt
l = ptt.l


_PREPROCESSED_DIR_PATH = 'preprocessed'


def preprocess_to_json_file(html_path):

    l.info('Preprocessing {}'.format(html_path))

    basename = to_basename(html_path)
    root, ext = splitext(basename)
    json_path = path_join(_PREPROCESSED_DIR_PATH, '{}.json'.format(root))

    if exists(json_path):
        l.info('Existed and skip {}'.format(json_path))
        return

    # read, parse,

    with open(html_path) as f:

        try:
            parsed_article_d = ptt.parse_article_page(f)
        except:
            l.info('Exception and skip {}'.format(json_path))
            return

    # and transform

    while 1:

        try:
            with open(json_path, 'w') as f:
                json.dump(parsed_article_d, f)
        except FileNotFoundError:
            mkdir(_PREPROCESSED_DIR_PATH)
            continue
        else:
            l.info('Wrote into {}'.format(json_path))

        break


def preprocess_all(html_dir_path):

    for dir_entry in scandir(html_dir_path):

        path = dir_entry.path

        if 'index' in path:
            continue

        preprocess_to_json_file(dir_entry.path)


if __name__ == '__main__':

    preprocess_all('cache')
