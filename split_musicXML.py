from music21 import *
from music21.stream import Score, Part
import os
import argparse
from tqdm import tqdm

"""
Split a MusicXML file into multiple by n bars
"""


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-o'
        '--output',
        dest='output',
        type=str,
        help="Directory containing split files",
        nargs='?',
        default='output'
    )

    parser.add_argument(
        '-f',
        '--file',
        dest='file',
        nargs='?',
        default='./beethoven_sonatas/sonata01-2.musicxml'
    )

    parser.add_argument(
        '-b'
        '--bars',
        dest='bars',
        type=int,
        default='4'
    )

    return parser.parse_args()


def split_in_fragments(score_path, output_dir, fragment_size):
    # Load the music score
    score = converter.parse(score_path)

    # Get the measures and time signatures
    measures_rh = score.parts[0].getElementsByClass(stream.Measure)
    measures_lh = score.parts[1].getElementsByClass(stream.Measure)

    fragments = []
    for idx in range(0, len(measures_rh) - fragment_size, fragment_size):
        fragments.append(
            Score([Part(measures_rh[idx:idx+4]), Part(measures_lh[idx:idx+4])]))

    filename = os.path.basename(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # Print the fragments
    for fragment in tqdm(fragments):
        fragment.write("musicxml", f'{output_dir}/{filename}'.split(
            '.')[0] + '_fragment_' + str(fragments.index(fragment)) + '.musicxml')


if __name__ == '__main__':
    args = parse_args()
    split_in_fragments(args.file, args.output, args.bars)
