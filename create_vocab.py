import os
import glob
import argparse
from tqdm import tqdm

def get_unique_strings(lists_of_strings):
    if lists_of_strings is None:
        return []

    unique_strings = set()
    for sub_list in lists_of_strings:
        for string in sub_list:
            if string is not None:
                unique_strings.add(string)
    return sorted(list(unique_strings))


def write_to_file(strings, filename):
    with open(filename, "w") as file:
        for string in strings:
            file.write(string + "\n")


def create_mappings(output_folder, tokens_list, unique_tokens):
    for i, tokens in enumerate(tokens_list):
        with open(os.path.join(output_folder, 'file' + str(i).zfill(3)) + '.txt', 'w') as file:
            for token in tokens:
                try:
                    file.write(str(unique_tokens.index(token)) + ' ')
                except ValueError as v:
                    continue