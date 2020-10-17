"""
Generate sequences based on trained models

author: William Tong (wlt2115@columbia.edu)
"""
import pickle
from pathlib import Path

from music21 import bar
from music21 import chord
from music21 import note
from music21 import stream
from music21 import tie

import numpy as np
import scipy

from .common import BayesianGaussianTypeModel

REST_WORD = 'REST'
START_WORD = 'START'
END_WORD = 'END'

norm_prob_cache = {}

def load_model(path: Path) -> 'Any':
    with path.open('rb') as fp:
        return pickle.load(fp)


def to_token(types, mixture, embedding):
    words = []
    for symbol in types:
        new_vec = mixture.emit(symbol, words) # instantiate and use previous words
        words.append(_decode(embedding, new_vec))
    print('raw_words', words)
    token_seq = [word.split('_') for word in words]

    return token_seq


def _decode(embedding, vector):
    return embedding.similar_by_vector(vector, topn=1)[0][0]


def to_score(token_seq, texture, **texture_args):
    score = stream.Stream()
    for note in texture(token_seq, **texture_args):
        score.append(note)

    return score


def chord_texture(token_seq, duration=1):
    for token in token_seq:
        if token[0] == REST_WORD:
            yield note.Rest()
        elif token[0] in (START_WORD, END_WORD):
            yield bar.Barline('double')
        else:
            print('processing token', token)
            yield chord.Chord(set(token), quarterLength=duration)


def chord_with_ties_texture(token_seq, duration=1):
    chords = chord_texture(token_seq, duration)
    chords_with_ties = []

    prev = next(chords)
    for stack in chords:
        if type(stack) is chord.Chord:
            for elem in prev:
                if elem in stack:
                    elem.tie = tie.Tie()
            chords_with_ties.append(prev)
            prev = stack

    chords_with_ties.append(prev)
    return chords_with_ties


def melody_texture(token_seq, duration=0.25, use_last=False):
    for token in token_seq:
        if token[0] == REST_WORD:
            yield note.Rest()
        elif token[0] in (START_WORD, END_WORD):
            yield bar.Barline('double')
        else:
            if use_last:
                yield(note.Note(token[-1], quarterLength=duration))
            else:
                for elem in token:
                    yield(note.Note(elem, quarterLength=duration))



if __name__ == '__main__':
    embedding = load_model(Path('save/embedding.wv'))
    mixture = BayesianGaussianTypeModel(embedding)
    mixture.load_model(Path('save/mixture.pk'))
    hmm = load_model(Path('save/hmm.pk'))

    types, _ = hmm.sample(10)
    types = types.flatten()
    print('Sampled', types)

    tokens = to_token(types, mixture, embedding)
    print('tokens', tokens)
    score = to_score(tokens, melody_texture)
    score.show('musicxml')
