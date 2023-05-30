from music21 import corpus, stream, converter, chord
from difflib import SequenceMatcher
import os
from tqdm import tqdm
import pickle

def get_chord_pitches(chord):
    notes = chord.notes
    midi = [note.pitch.midi for note in notes]
    return midi

def get_midi_pitches(part):
    midi_pitches = []
    for obj in part.flatten().notes:
        if isinstance(obj, chord.Chord):
            chord_midi = get_chord_pitches(obj)
            midi_pitches.extend(chord_midi)
        else:
            midi_pitches.append(obj.pitch.midi)

    return midi_pitches

def get_piano_pitches(path):
    score = converter.parse(path)
    left_hand, right_hand = score.parts[0], score.parts[1]
    midi_lh = get_midi_pitches(left_hand)
    #midi_rh = get_midi_pitches(right_hand)
    return midi_lh

def process_pitches(path_list, output_file):
    pitches_list = [get_piano_pitches(path) for path in tqdm(path_list)]

    with open(output_file, 'wb') as f:
        pickle.dump(pitches_list, f)

    return pitches_list


def compute_similarity(l1, l2):
    similarity_score = SequenceMatcher(a=l1, b=l2)
    return similarity_score.quick_ratio()
