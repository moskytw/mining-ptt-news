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


_TARGETS_DIR_PATH = 'targets'


def generate_target_from(json_path):

    l.info('Generate target from {} ...'.format(json_path))

    basename = to_basename(json_path)
    root, ext = splitext(basename)
    txt_path = path_join(_TARGETS_DIR_PATH, '{}.txt'.format(root))

    if exists(txt_path):
        l.info('Existed and skip {}'.format(txt_path))
        return

    with open(json_path) as f:
        d = json.load(f)
        push_score_sum = sum(push_d['score'] for push_d in d['push_ds'])

    with ptt_core.mkdir_n_open(txt_path, 'w') as f:
        f.write(str(push_score_sum))
    l.info('Wrote into {}'.format(txt_path))


def generate_all(preprocessed_dir_path):

    for dir_entry in scandir(preprocessed_dir_path):
        generate_target_from(dir_entry.path)


if __name__ == '__main__':

    generate_all('preprocessed')
