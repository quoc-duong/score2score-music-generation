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
from process_musescore import parse_args, get_mscz_paths


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

    piano = 0
    not_piano = 0
    # Iterate over the filenames
    for filename in tqdm(filenames):
        # Extract the ID from the filename
        file_id = os.path.splitext(os.path.basename(filename))[0]
        # Look up the corresponding JSON object in the lookup table using the ID as the key
        if file_id in lookup:
            # Check if the instrumentsNames field contains "Piano"
            if lookup[file_id]["instrumentsNames"] == ['Piano'] or lookup[file_id]["instrumentsNames"] == ['piano']:
                piano += 1
            else:
                if os.path.exists(filename):
                    os.remove(filename)
                    not_piano += 1

    print(f'Got {piano} piano scores')
    print(f'Removed {not_piano} scores')


def remove_all_mscz(dir_path):
    # Loop through each file and directory in the folder
    for root, dirs, files in os.walk(dir_path):
        # Loop through each file and remove files with a .mscz extension
        for file in files:
            if file.endswith('.mscz'):
                os.remove(os.path.join(root, file))


def main():
    args = parse_args()
    path = os.path.expanduser(args.dir_path)
    #file_list = get_mscz_paths(path)
    #filter_piano(file_list, args.metadata)
    remove_all_mscz(path)


if __name__ == "__main__":
    main()
