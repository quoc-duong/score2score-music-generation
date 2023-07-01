from music21 import *
from music21.stream import Score, Part
import os
import argparse
from tqdm import tqdm
import glob
import numpy as np
import pandas as pd
from score_to_tokens import MusicXML_to_tokens
from create_vocab import *

"""
Split a MusicXML file into multiple by n bars

Create vocabulary file from MusicXML data

Convert MusicXML data into Score Transformers representation
then creates a vocabulary file from that.
"""

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-o'
        '--output',
        dest='output',
        type=str,
        help="Directory containing split files",
        nargs='?',
        default='dataset_fragments'
    )

    parser.add_argument(
        '-d',
        '--dir',
        dest='dir',
        nargs='?',
        default='./dataset_musicxml_filtered/'
    )

    parser.add_argument(
        '--difficulty',
        dest='difficulty',
        nargs='?',
        default='data/difficulties_filtered.pkl'
    )

    parser.add_argument(
        '-b'
        '--bars',
        dest='bars',
        type=int,
        default='4'
    )

    parser.add_argument(
        '--musicxml',
        dest='musicxml',
        type=dir_path,
        help='Directory containing MusicXML data',
        default='dataset_fragments_4'
    )

    parser.add_argument(
        '-m'
        '--mapped',
        dest='mapped',
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
        default='mapped/score_transformers_vocab.txt'
    )

    return parser.parse_args()


def split_in_fragments(score_path, output_dir, fragment_size, difficulty_dict):
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
                '.')[0] + '_fragment_' + str(fragments.index(fragment) + '_d_' + str(difficulty_dict.get(score_path))) + '.musicxml')
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

def create_tuple_dictionary(tuple_list):
    tuple_dict = {t[0]: t[1] for t in tuple_list}
    return tuple_dict

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
    args = parse_args()

    with open(args.difficulty, 'rb') as f:
        difficulty_dict = create_tuple_dictionary(pickle.dump(f))

    for f in tqdm(os.listdir(args.dir), 'Splitting musicxml score into fragments'):
        filepath = os.path.join(args.dir, f)
        split_in_fragments(filepath, args.output, args.bars, difficulty_dict)

    musicxml_path = args.musicxml
    filepaths = glob.glob(musicxml_path + '/*')

    tokens_list = []
    for path in tqdm(filepaths):
        try:
            sub_list = MusicXML_to_tokens(path)
            if sub_list is not None:
                tokens_list.append(sub_list)
        except Exception as e:
            continue

    unique_tokens = get_unique_strings(tokens_list)

    os.makedirs(args.mapped, exist_ok=True)

    write_to_file(unique_tokens, args.vocab)

    create_mappings(args.mapped, tokens_list, unique_tokens)

if __name__ == '__main__':
    main()
