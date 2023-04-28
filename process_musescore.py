import os
import subprocess
import pandas as pd
import argparse
import getch
import signal
import json
from tqdm import tqdm
import pickle
import re
import music21
import shutil


def parse_args():
    # Set up argparse
    parser = argparse.ArgumentParser(description='Process Musescore files')
    parser.add_argument('--dir_path',
                        default='~/Documents/upf/MuseScore',
                        type=str,
                        help='Path to directory containing Musescore files')
    parser.add_argument('--metadata',
                        default='./data/score.jsonl',
                        type=str,
                        help='Path to metadata file')
    parser.add_argument('--csv_path',
                        default='./data/score_annotation.csv',
                        type=str,
                        help='Path to output CSV file')
    parser.add_argument('--process',
                        action='store_true',
                        help='Retrieve piano only scores and store in a pickle file (piano_only.pkl)')
    parser.add_argument('--convert',
                        action='store_true',
                        help='Convert mscz files to musicxml')
    return parser.parse_args()


def filter_piano(filenames, metadata):
    lookup = {}

    with open(metadata) as f:
        # Parse each line in the file
        for line in tqdm(f):
            # Parse the JSON in the line
            data = json.loads(line)
            # Add the JSON object to the lookup table using the authorUserId as the key
            try:
                lookup[data["id"]] = data
            except KeyError:
                pass

    piano = []
    # Iterate over the filenames
    for filename in tqdm(filenames):
        # Extract the ID from the filename
        file_id = os.path.splitext(os.path.basename(filename))[0]
        # Look up the corresponding JSON object in the lookup table using the ID as the key
        if file_id in lookup:
            # Check if the instrumentsNames field contains "Piano"
            if lookup[file_id]["instrumentsNames"] == ['Piano'] or lookup[file_id]["instrumentsNames"] == ['piano']:
                piano.append(filename)
    print(f'Got {len(piano)} piano scores')
    return piano


def get_mscz_paths(dir_path):
    # Get list of all subdirectories in directory
    subdir_list = [f.path for f in os.scandir(dir_path) if f.is_dir()]

    # Iterate through subdirectories and get list of .mscz files in each
    file_list = []
    for subdir in subdir_list:
        subdir_files = [os.path.join(subdir, f) for f in os.listdir(
            subdir) if f.endswith('.mscz')]
        file_list += subdir_files
    return file_list


def mscz2musicxml(scores, json_name):
    to_discard = []
    pattern = r"\/\w+(?:\/\w+)*\/\d+\.\w+"
    json_batch = create_convert_batch(scores, to_discard)
    with open(json_name, 'w') as f:
        json.dump(json_batch, f)
    while True:
        mscore_process = subprocess.Popen(
            ['musescore.mscore', '-j', json_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print('Waiting to finish')

        # Print live output of the subprocess
        while True:
            output = mscore_process.stdout.readline()
            if output == b'' and mscore_process.poll() is not None:
                break
            last_line = output
            if output:
                output = output.decode("utf-8").strip()
                print(output)  # Subprocess output
                match = re.search(pattern, output)
                if match:
                    problematic_file = match.group(0)

        if mscore_process.returncode != 0:
            print('Job stopped unexpectedly\n')
            if problematic_file not in to_discard:
                # Add file that's problematic to the discard list
                print(f"Discarding {problematic_file}")
                to_discard.append(problematic_file)

        print(f"There are {len(to_discard)} discarded file(s)")

        json_batch = create_convert_batch(scores, to_discard)
        if len(json_batch) == 0:
            break
        with open(json_name, 'w') as f:
            json.dump(json_batch, f)
    print('Done')


def create_convert_batch(score_list, to_discard):
    json_out = []

    for d in to_discard:
        filename = d.split('/')[-1]
        for i, item in enumerate(score_list):
            if filename == item.split('/')[-1]:
                score_list.pop(i)
                break

    for filename in tqdm(score_list):
        musicxml_name = filename.replace('.mscz', '.musicxml')
        if os.path.exists(musicxml_name):
            continue
        output = {}
        output['in'] = filename
        output['out'] = musicxml_name
        json_out.append(output)
    print(f"Job will process {len(json_out)} files")
    return json_out


def get_musicxml_paths(file_list):
    count = 0
    musicxml_paths = []
    for file in file_list:
        musicxml_file = os.path.splitext(file)[0] + '.musicxml'
        if os.path.exists(musicxml_file):
            musicxml_paths.append(musicxml_file)
            count += 1

    print(f'Total number of files with corresponding musicxml: {count}')
    return musicxml_paths


def filter_empty(scores):
    musicxml_paths = get_musicxml_paths(scores)
    filtered_paths = []
    for musicxml in tqdm(musicxml_paths):
        try:
            score = music21.converter.parse(musicxml)
        except music21.Music21Exception:
            continue
        except Exception:
            continue
        if len(score.parts) < 2:
            continue
        rh = score.parts[0].getElementsByClass(music21.stream.Measure)
        lh = score.parts[1].getElementsByClass(music21.stream.Measure)

        if len(rh) == 0 or len(lh) == 0:
            print("The staff is empty")
            print(musicxml)
        else:
            filtered_paths.append(musicxml)
    return filtered_paths


def create_filtered_pickle(filename, obj):
    filtered_musicxml = None
    if not os.path.exists(filename):
        filtered_musicxml = filter_empty(obj)
        with open(filename, 'wb') as f:
            pickle.dump(filtered_musicxml, f)
    else:
        with open(filename, 'rb') as f:
            filtered_musicxml = pickle.load(f)
    return filtered_musicxml


def create_dataset():
    # Create .mscz dataset
    with open('./data/piano.pkl', 'rb') as f:
        piano_mscz = pickle.load(f)

    os.makedirs('dataset_mscz', exist_ok=True)
    piano_dir = './dataset_mscz/piano'
    os.makedirs(piano_dir, exist_ok=True)

    for filepath in piano_mscz:
        shutil.copy(filepath, piano_dir)

    # Create MusicXML dataset
    with open('./data/filtered_piano.pkl', 'rb') as f:
        piano_musicxml = pickle.load(f)

    os.makedirs('dataset_musicxml', exist_ok=True)
    piano_dir = './dataset_musicxml/piano'
    os.makedirs(piano_dir, exist_ok=True)

    for filepath in piano_musicxml:
        shutil.copy(filepath, piano_dir)


def main():
    args = parse_args()
    piano = None
    piano_path = './data/piano.pkl'
    if args.process:
        path = os.path.expanduser(args.dir_path)
        file_list = get_mscz_paths(path)
        piano = filter_piano(
            file_list, args.metadata)
        with open(piano_path, 'wb') as f:
            pickle.dump(piano, f)
    else:
        if not os.path.exists(piano_path):
            raise Exception('Pickle file does not exist')
        with open(piano_path, 'rb') as f:
            piano = pickle.load(f)

    if args.convert:
        mscz2musicxml(piano, './data/piano.json')

    filtered_musicxml_piano = create_filtered_pickle(
        './data/filtered_piano.pkl', piano)

    print(f"There are {len(filtered_musicxml_piano)} piano files")

    create_dataset()


if __name__ == "__main__":
    main()
