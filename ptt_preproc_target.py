#!/usr/bin/env python


import json
from pathlib import Path
from os import scandir
from os.path import (
    join as path_join,
    basename as to_basename,
    splitext,
    exists
)

import ptt_core
l = ptt_core.l


_TARGETS_DIR_PATH = Path('targets')

if not _TARGETS_DIR_PATH.exists():
    _TARGETS_DIR_PATH.mkdir()


def generate_target_from(json_path):

    l.info('Generate target from {} ...'.format(json_path))

    txt_path = _TARGETS_DIR_PATH / '{}.txt'.format(json_path.stem)

    if txt_path.exists():
        l.info('Existed and skip {}'.format(txt_path))
        return

    with json_path.open() as f:
        d = json.load(f)
        push_score_sum = sum(push_d['score'] for push_d in d['push_ds'])

    with txt_path.open('w') as f:
        f.write(str(push_score_sum))
    l.info('Wrote into {}'.format(txt_path))


def generate_all(preprocessed_dir_path_str):

    for path in Path(preprocessed_dir_path_str).iterdir():
        generate_target_from(path)


if __name__ == '__main__':

    generate_all('preprocessed')
