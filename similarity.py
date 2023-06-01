from music21 import corpus, stream, converter, chord, Music21Exception
from difflib import SequenceMatcher
import os
from tqdm import tqdm
import pickle
import concurrent.futures

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
    #midi_lh = get_midi_pitches(left_hand)
    midi_rh = get_midi_pitches(right_hand)
    return (path, midi_rh)

def process_pitches(path_list, output_file, num_threads=os.cpu_count()):
    pitches_list = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        progress_bar = tqdm(total=len(path_list))

        futures = [executor.submit(get_piano_pitches, path) for path in path_list]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            progress_bar.update(1)

            if result is not None:
                pitches_list.append(result)

        progress_bar.close()

    with open(output_file, 'wb') as f:
        pickle.dump(pitches_list, f)

    print(f'Computed {len(pitches_list)} scores for pitches')

    return pitches_list


def compute_similarity(l1, l2):
    similarity_score = SequenceMatcher(a=l1, b=l2)
    return similarity_score.quick_ratio()
