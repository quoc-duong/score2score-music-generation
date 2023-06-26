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
        help='Directory containing MusicXML data',
        default='dataset_musicxml/piano/'
    )

    parser.add_argument(
        '-o'
        '--output',
        dest='output',
        type=str,
        help="Directory containing mapped data",
        nargs='?',
        default='mapped'
    )

    parser.add_argument(
        '-v',
        '--vocab',
        dest='vocab',
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


def create_mappings(output_folder, tokens_list, unique_tokens):
    for i, tokens in enumerate(tokens_list):
        os.makedirs(output_folder, exist_ok=True)
        with open(os.path.join(output_folder, 'file' + str(i).zfill(3)) + '.txt', 'w') as file:
            for token in tokens:
                file.write(str(unique_tokens.index(token)) + ' ')


def main():
    args = parse_args()
    musicxml_path = args.musicxml

    filepaths = glob.glob(musicxml_path + '/*')

    tokens_list = [MusicXML_to_tokens(path) for path in tqdm(filepaths)]

    unique_tokens = get_unique_strings(tokens_list)

    write_to_file(unique_tokens, args.vocab)

    create_mappings(args.output, tokens_list, unique_tokens)


if __name__ == "__main__":
    main()
