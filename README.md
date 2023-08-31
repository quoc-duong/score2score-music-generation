# score2score-music-generation

## Description

This is the repository associated to the thesis on Automatic score-to-score music generation at UPF.

Here, you can find tools to process musescore data, do tokenization and create a dataset for training.

## Usage

### process_musescore.py

```
python process_musescore.py --convert --process
```

The `--process` option retrieves all `.mscz` files, retrieves piano only files and stores them in a pickle file.

The `--convert` option makes use of the pickle file generated from the `--process` step and converts all `.mscz` files into the MusicXML format using the `mscore` tool from MuseScore. The script discards corrupted files.
