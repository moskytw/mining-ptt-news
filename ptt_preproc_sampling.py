#!/usr/bin/env python


from pathlib import Path
from random import sample
from os import remove


# configs

N = 10000

# remove unsampled

paths = [path for path in Path('preprocessed/').iterdir()]
paths_len = len(paths)

if paths_len <= N:
    raise RuntimeError('file count {:,} <= N {:,}'.format(paths_len, N))

for path in sample(paths, paths_len-N):
    remove(str(path))
