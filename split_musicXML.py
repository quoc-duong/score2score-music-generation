from music21 import *
from music21.stream import Score, Part
import os
import argparse
from tqdm import tqdm
import glob
import numpy as np
import pandas as pd

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
        '-d',
        '--dir',
        dest='dir',
        nargs='?',
        default='./beethoven_sonatas/'
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
    for idx in range(0, len(measures_rh) - fragment_size + 1, fragment_size):
        fragments.append(
            Score([Part(measures_rh[idx:idx+4]), Part(measures_lh[idx:idx+4])]))

    filename = os.path.basename(score_path)
    os.makedirs(output_dir, exist_ok=True)
    # Print the fragments
    for i, fragment in enumerate(tqdm(fragments)):
        try:
            fragment.write("musicxml", f'{output_dir}/{filename}'.split(
                '.')[0] + '_fragment_' + str(fragments.index(fragment)) + '.musicxml')
        except musicxml.xmlObjects.MusicXMLException as e:
            print(f"MusicXML error on fragment {i}: {e}")
            pass
        except Exception as e:
            print(f"Other error on fragment {i}: {e}")
            pass


def create_complexity_all(fragments_path):
    df = pd.DataFrame(columns=['complexity'])
    for filepath in tqdm(glob.glob(fragments_path + '/*')):
        fragment = converter.parse(filepath)
        complexity = compute_complexity(fragment)
        df.loc[filepath] = complexity

    return df


def compute_complexity(fragment):
    complexity_values = []
    measures_rh = fragment.parts[0].getElementsByClass(stream.Measure)
    measures_lh = fragment.parts[1].getElementsByClass(stream.Measure)
    lr = [Part(measures_lh), Part(measures_rh)]
    for voice in lr:
        # Convert the voice to a pitch array
        note_array = np.array(
            [e.duration.quarterLength / len(e.pitches) if e.isChord else e.duration.quarterLength for e in voice.flat.notes.stream()])

        if not len(note_array):
            complexity_values.append(0)
            continue

        complexity_values.append(len(note_array) / sum(note_array))

    # Return the average note complexity across all voices
    return np.mean(complexity_values)


def main():
    # for filepath in glob.glob(args.dir + '/*'):
    #    split_in_fragments(filepath, args.output, args.bars)
    df = create_complexity_all(args.output)
    df.to_csv('complexity.csv')
    #fragment = converter.parse('output/sonata16-1_fragment_29.musicxml')
    # print(compute__complexity(fragment))
    #fragment = converter.parse('output/sonata01-1_fragment_0.musicxml')
    # print(compute_complexity(fragment))


if __name__ == '__main__':
    args = parse_args()
    main()
