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
import concurrent.futures
import threading
from similarity import process_pitches


def parse_args():
    # Set up argparse
    parser = argparse.ArgumentParser(description='Process Musescore files')
    parser.add_argument('--dir_path',
                        default='~/Documents/upf/MuseScore',
                        type=str,
                        help='Path to directory containing Musescore files')
    parser.add_argument('--pkl',
                        default='./data/piano_musicxml.pkl',
                        type=str,
                        help='Pickle file containing list of filtered MusicXML piano files')
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
    parser.add_argument('--filter_empty',
                        action='store_true',
                        help='Filter out empty musicxml files')
    parser.add_argument('--musicxml_data',
                        action='store_true',
                        help='Use musicxml converted files')
    return parser.parse_args()


def filter_piano(filenames, metadata):
    '''
    Function to filter out files that are not piano (looking at the MuseScore metadata)
    '''
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
    '''
    Get list of .mscz files
    '''
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
    '''
    Convert all MuseScore files into MusicXML files in the same folders
    Handles corrupt files and errors with mscore process.
    TODO: Catch subprocess freezing
    '''
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
    '''
    Create JSON batch file for the conversion with mscore
    '''
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


def get_musicxml_paths(data_path):
    '''
    Get list of .mscz files
    '''
    count = 0
    musicxml_files = []
    for root, _, files in os.walk(data_path):
        for file in files:
            if file.endswith('.musicxml'):
                musicxml_files.append(os.path.join(root, file))
                count += 1

    print(f'Total number of musicxml files: {count}')
    return musicxml_files


def is_piano(musicxml):
    try:
        score = music21.converter.parse(musicxml)
    except music21.Music21Exception:
        return None
    except Exception:
        return None
    if len(score.parts) != 2:  # Ignore files that don't have 2 parts (left/right hand of piano)
        return None
    rh = score.parts[0].getElementsByClass(music21.stream.Measure)
    lh = score.parts[1].getElementsByClass(music21.stream.Measure)

    if len(rh) == 0 or len(lh) == 0:
        print("The staff is empty")
        return None
    return musicxml


def filter_empty(data_path, num_threads=os.cpu_count()):
    '''
    Filter out files that either have empty staves or don't have exactly 2 staves (left/right hand)
    '''
    musicxml_paths = get_musicxml_paths(data_path)
    results = []
    threads = []

    for file in tqdm(musicxml_paths):
        thread = threading.Thread(target=results.append(is_piano(file)))
        threads.append(thread)

        if len(threads) >= num_threads:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = []
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def create_filtered_pickle(filename, data_path):
    '''
    Create pickle file containing the list of filtered piano paths
    '''
    filtered_musicxml = None
    if not os.path.exists(filename):
        filtered_musicxml = filter_empty(data_path)
        with open(filename, 'wb') as f:
            pickle.dump(filtered_musicxml, f)
    else:
        with open(filename, 'rb') as f:
            filtered_musicxml = pickle.load(f)
    return filtered_musicxml


def create_dataset():
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
    path = os.path.expanduser(args.dir_path)
    if args.process:
        file_list = get_mscz_paths(path)
        piano = filter_piano(
            file_list, args.metadata)
        with open(piano_path, 'wb') as f:
            pickle.dump(piano, f)

    if args.convert:
        if not args.process:
            if not os.path.exists(piano_path):
                raise Exception('Pickle file does not exist')
            with open(piano_path, 'rb') as f:
                piano = pickle.load(f)
        mscz2musicxml(piano, './data/piano.json')

    if args.filter_empty:
        piano_musicxml = create_filtered_pickle(args.pkl, path)
        print(f"There are {len(piano_musicxml)} piano files")
    else:
        if args.musicxml_data:
            piano_musicxml = get_musicxml_paths(path)
        else:
            with open(args.pkl, 'rb') as f:
                piano_musicxml = pickle.load(f)

    process_pitches(piano_musicxml,  './data/pitches.pkl')

    # create_dataset()


if __name__ == "__main__":
    main()
