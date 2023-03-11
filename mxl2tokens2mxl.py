from score_to_tokens import MusicXML_to_tokens
from tokens_to_score import tokens_to_score


def main():
    tokens = MusicXML_to_tokens('beethoven_sonatas/sonata01-1.musicxml')
    score = tokens_to_score(' '.join(tokens))
    score.write('musicxml', 'generated_test')


if __name__ == "__main__":
    main()
