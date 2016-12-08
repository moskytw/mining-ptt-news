# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import itertools
import json
import re 

import jieba
import zhon.hanzi

def generate_corpus(preprocessed_dir_path, targets_dir_path, corpus_outputfile_path, targets_outputfile_path):
    for i, f in enumerate(preprocessed_dir_path.glob('*.json'), 1):
        content_s = json.load(f.open())['title']
        print(preprocess_and_tokenizie(content_s), file=corpus_outputfile_path.open(mode='a', encoding='utf-8'))
        targets_file_path = targets_dir_path / (f.stem + '.txt')
        print(targets_file_path.read_text(), file=targets_outputfile_path.open(mode='a', encoding='utf-8'))
        print(str(i), f.stem)


def preprocess_and_tokenizie(raw_s):
    no_link_s = re.sub(r'https?:\/\/(.+\.)+(.+\/)+([\S]+\/?)', '', raw_s)
    sents_list = [x.replace('\n', '') for x in no_link_s.split('\n\n')]
    sents_list = [re.sub('[%s]' % zhon.hanzi.punctuation, ' ', x) for x in sents_list] # replace punctuation to spaces
    sents_list = [''.join(re.findall(r'[%s]' % (zhon.hanzi.characters + 'a-zA-Z0-9 ') , x)) for x in sents_list]
    sents_list = filter(lambda x: len(x)!=0, itertools.chain(*[x.split(' ') for x in sents_list]))
    return ' '.join([' '.join(jieba.cut(x)) for x in sents_list]) 


if __name__ == '__main__':
    cml_parser = argparse.ArgumentParser()
    cml_parser.add_argument('--preprocessed-dir', 
        help='preprossed files directory', 
        type=str, metavar='PATH', required=True
    )
    cml_parser.add_argument('--targets-dir',
        help="targets directory",
        type=str, metavar='PATH', required=True
    )
    cml_parser.add_argument('--corpus-output',
        help='output file of corpus',
        type=str, metavar='PATH', required=True
    )
    cml_parser.add_argument('--target-output',
        help='output file for targets',
        type=str, metavar='PATH', required=True
    )

    args = cml_parser.parse_args()
    jieba.set_dictionary('dict.txt.big')
    generate_corpus(Path(args.preprocessed_dir), Path(args.targets_dir), Path(args.corpus_output), Path(args.target_output))   

    
