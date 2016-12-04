#!/usr/bin/env python


import json
import sys
from os import scandir, remove
from datetime import datetime


START_DT = datetime(2016, 7, 1, 0, 0, 0)
END_DT = datetime(2016, 12, 1, 0, 0, 0)
DRY_RUN = True


for dir_entry in scandir('preprocessed'):

    path = dir_entry.path
    with open(path) as f:

        # read the json into d

        try:
            d = json.load(f)
        except:
            print('[Error]', path, sep='\t', file=sys.stderr)
            continue

        # decide keep or remove

        authores_dt = datetime.fromtimestamp(d['authored_ts'])
        # print [DATETIME]    path    KEEP|REMOVE    DRY_RUN?
        print(authores_dt, path, sep='\t', end='\t')
        if START_DT <= authores_dt < END_DT:
            print('KEEP')
        else:
            if DRY_RUN:
                print('REMOVE', 'DRY_RUN', sep='\t')
            else:
                print('REMOVE', sep='\t')
                remove(path)
