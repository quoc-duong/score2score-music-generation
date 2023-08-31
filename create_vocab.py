import os
import glob
import argparse
from tqdm import tqdm

def get_unique_strings(lists_of_strings):
    if lists_of_strings is None:
        return []

    unique_strings = set()
    for _, sub_list in lists_of_strings:
        for string in sub_list:
            if string is not None:
                unique_strings.add(string)
    return sorted(list(unique_strings))


def write_to_file(strings, filename):
    with open(filename, "w") as file:
        for string in strings:
            file.write(string + "\n")


def create_mappings(output_folder, tokens_list, unique_tokens):
    for i, obj in enumerate(tqdm(tokens_list, 'Create mapping files')):
        path, tokens = obj
        with open(os.path.join(output_folder, os.path.splitext(os.path.basename(path))[0] + '.txt'), 'w') as f:
            f.write(str(tokens[0]) + ' ')
            for i in range(1, len(tokens)):
                try:
                    f.write(str(unique_tokens.index(tokens[i])) + ' ')
                except ValueError as v:
                    continue