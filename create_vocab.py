""" Create vocabulary file from MusicXML data

This script allows to convert MusicXML data into Score Transformers representation
then creates a vocabulary file from that.

"""

import os
import glob
import argparse
from tqdm import tqdm
from score_to_tokens import MusicXML_to_tokens


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--musicxml',
        dest='musicxml',
        type=dir_path,
        help="Directory containing MusicXML data"
    )

    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        nargs='?',
        default='score_transformers_vocab.txt'
    )

    return parser.parse_args()


def get_unique_strings(lists_of_strings):
    unique_strings = set()
    for sub_list in lists_of_strings:
        for string in sub_list:
            unique_strings.add(string)
    return sorted(list(unique_strings))


def write_to_file(strings, filename):
    with open(filename, "w") as file:
        for string in strings:
            file.write(string + "\n")


def main():
    args = parse_args()
    musicxml_path = args.musicxml

    sonatas_paths = glob.glob(musicxml_path + '/*')

    tokens_list = [MusicXML_to_tokens(path) for path in tqdm(sonatas_paths)]

    unique_tokens = get_unique_strings(tokens_list)
    write_to_file(unique_tokens, args.output)


if __name__ == "__main__":
    main()
