from music21 import corpus, stream, converter, chord, Music21Exception
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
    try:
        score = converter.parse(path)
    except Music21Exception:
        return None
    except Exception:
        return None

    if len(score.parts) != 2:
        return None
    left_hand, right_hand = score.parts[1], score.parts[0]
    midi_lh = get_midi_pitches(left_hand)
    #midi_rh = get_midi_pitches(right_hand)
    return midi_lh

def process_pitches(path_list, output_file):
    pitches_list = [(path, value) for path in tqdm(path_list) if (value := get_piano_pitches(path)) is not None]

    with open(output_file, 'wb') as f:
        pickle.dump(pitches_list, f)

    return pitches_list


def compute_similarity(l1, l2):
    similarity_score = SequenceMatcher(a=l1, b=l2)
    return similarity_score.quick_ratio()
