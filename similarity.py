from music21 import corpus, stream, converter, chord, Music21Exception, note
from difflib import SequenceMatcher
from datasketch import MinHash, MinHashLSH
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
        elif isinstance(obj, note.Note):
            midi_pitches.append(obj.pitch.midi)

    if len(midi_pitches) == 0:
        return None
    return midi_pitches

def get_piano_pitches(path, is_right_hand=True):
    try:
        score = converter.parse(path)
    except Music21Exception:
        return None
    except Exception:
        return None

    if len(score.parts) != 2:
        return None
    left_hand, right_hand = score.parts[1], score.parts[0]

    midi = None
    if is_right_hand:
        midi = get_midi_pitches(right_hand)
    else:
        midi = get_midi_pitches(left_hand)
    if midi is None:
        return None
    return (path, midi)

def process_pitches(path_list, output_file, is_right_hand=True, num_threads=os.cpu_count()):
    pitches_list = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        progress_bar = tqdm(total=len(path_list))

        futures = [executor.submit(get_piano_pitches, path, is_right_hand) for path in path_list]
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
    len1, len2 = len(l1), len(l2)
    len_diff = abs(len1 - len2)
    max_len = max(len1, len2)
    length_weight = 1 - (len_diff / max_len)

    matcher = SequenceMatcher(a=l1, b=l2)
    similarity_score = matcher.ratio()

    weighted_similarity = similarity_score * length_weight
    return weighted_similarity

def compute_minhash(pitches):
    set_list = [set(el[1]) for el in pitches]
    minhashes = []

    for seq in tqdm(set_list, 'Minhashing pitches'):
        minhash = MinHash(num_perm=128)
        for number in seq:
            minhash.update(str(number).encode('utf-8'))
        minhashes.append(minhash)


    lsh = MinHashLSH(threshold=1, num_perm=128)
    for i, minhash in enumerate(tqdm(minhashes)):
        lsh.insert(i, minhash)

    return lsh, minhashes

def sort_pitches(pitches):
    return sorted(pitches, key=lambda x: len(x[1]), reverse=True)

def process_similarity(pitch_path='./data/pitches.pkl', threshold=0.01):
    with open(pitch_path, 'rb') as f:
        pitches = pickle.load(f)

    # Longer files are first
    pitches = sort_pitches(pitches)

    lsh, minhashes = compute_minhash(pitches)

    to_remove = set()
    processed = set()

    similarities = []
    for i, p in tqdm(enumerate(pitches), 'Storing similar files (MinHash)'):
        similar_indices = lsh.query(minhashes[i])
        similar_sequences = [pitches[i] for i in similar_indices]
        similarities.append([p] + similar_sequences)

    for l in tqdm(similarities, 'Computing edit distance for similar files'):
        main_path, main_pitch_list = l[0]
        if main_path in processed:
            continue
        processed.add(main_path)
        for i in range(1, len(l)):
            current_path, current_pitch_list = l[i]
            if current_path in processed:
                continue
            score = compute_similarity(main_pitch_list, current_pitch_list)
            if score >= threshold:
                to_remove.add(l[i][0])
                processed.add(current_path)


    print(f'There are {len(to_remove)} files to remove from the dataset')

    results = [tup for tup in pitches if tup[0] not in to_remove]

    paths, pitches = zip(*results)

    return list(paths)