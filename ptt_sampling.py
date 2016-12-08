#!/usr/bin/env python


from pathlib import Path
from random import shuffle
from shutil import copy


# configs

N = 10000
SAMPLED_DIR_PATH = Path('sampled/')

# mkdir if doesn't exist

if not SAMPLED_DIR_PATH.exists():
    SAMPLED_DIR_PATH.mkdir()

# sample and copy

paths = [p for p in Path('preprocessed/').iterdir()]
shuffle(paths)

for p in paths[:N]:
    copy(str(p), str(SAMPLED_DIR_PATH / p.name))
