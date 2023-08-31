import os
import glob
import argparse
from tqdm import tqdm
from tokens_to_score import tokens_to_score


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--preds',
        dest='preds',
        type=str,
        help='prediction file'
    )

    parser.add_argument(
        '-o'
        '--output',
        dest='output',
        type=str,
        help="Directory containing mapped data",
        nargs='?',
        default='output_xml'
    )

    parser.add_argument(
        '-v',
        '--vocab',
        dest='vocab',
        nargs='?',
        default='data/score_transformers_vocab.txt'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    unique_tokens = []
    with open(args.vocab, "r") as file:
        for line in file:
            unique_tokens += line.rstrip().split()

    score_representation = []
    with open(args.preds, "r") as file:
        for line in file:
            score_representation += line.split()

    for i in range(len(score_representation)):
        score_representation[i] = unique_tokens[int(score_representation[i])]

    score_string = ' '.join(score_representation)
    score = tokens_to_score(score_string)
    score.write('musicxml', 'generated_score')


if __name__ == "__main__":
    main()
