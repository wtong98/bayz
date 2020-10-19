"""
Generate sequences based on trained models. Ensure you first have 'save/'
in your current working directory, containing saved model files. If not,
first run

$ python -m bayz.train

then

$ python -m bayz.generate

to generate a short sample of music. In order to display the music, ensure
you have a working musicxml renderer configured with music21. For instructions
on how, see: https://web.mit.edu/music21/doc/usersGuide/usersGuide_08_installingMusicXML.html

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
    """
    Load a model file from the given path

    path: a pathlib.Path object
    return: the loaded model
    """

    with path.open('rb') as fp:
        return pickle.load(fp)


def to_token(types: list, mixture: BayesianGaussianTypeModel, embedding: 'Word2Vec') -> list:
    """
    Samples a set of tokens from the provided mixture model

    param types: a list of types (mixture ids) corresponding to the music to be
                 generated
    param mixture: a mixture model fitted to a training corpus
    param embedding: a Word2Vec model trained on the corpus

    return: a list of abstract note names, ready to be sampled into real music
    """

    words = []
    for symbol in types:
        new_vec = mixture.emit(symbol, words) # instantiate and use previous words
        words.append(_decode(embedding, new_vec))
    token_seq = [word.split('_') for word in words]

    return token_seq


def _decode(embedding, vector):
    return embedding.similar_by_vector(vector, topn=1)[0][0]


def to_score(token_seq: list, texture: 'function', **texture_args) -> 'Score':
    """
    Samples a music21.Score object from a list of tokens

    param token_seq: list of tokens
    param texture: a function that determines the texture with which to give
                   the sampled music
    param **texture_args: arguments passed to the texture function

    return: a generated music21.Score object
    """

    score = stream.Stream()
    for note in texture(token_seq, **texture_args):
        score.append(note)

    return score


def chord_texture(token_seq, duration=1):
    """
    Defines a texture in which tokens are rendered as chords

    param token_seq: tokens to be rendered
    param duration: the duration of each chord
    """

    for token in token_seq:
        if token[0] == REST_WORD:
            yield note.Rest()
        elif token[0] in (START_WORD, END_WORD):
            yield bar.Barline('double')
        else:
            print('processing token', token)
            yield chord.Chord(set(token), quarterLength=duration)


def chord_with_ties_texture(token_seq, duration=1):
    """
    Defines a texture in which tokens are rendered as chords. Adjacent chords
    with shared notes have ties that connect the notes, creating a continuous
    sound.

    param token_seq: tokens to be rendered
    param duration: the duration of each chord
    """

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
    """
    Defines a texture in which tokens are rendered as individual notes

    param token_seq: tokens to be rendered
    param duration: the duration of each chord
    param use_last: whether to sample notes from the last note of each word, or
                    to use all notes in a word
    """

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


def to_midi(token_seq: list, use_last=False) -> list:
    """
    Renders a set of tokens directly into midi values, rather than a Score. It
    uses the same scheme as the melody_texture.

    param token_seq: tokens to be rendered
    param use_last: whether to sample the last note in a word, or to use the
                    entire word
    
    return: list of midi note values
    """

    for token in token_seq:
        if token[0] != REST_WORD or token[0] not in (START_WORD, END_WORD):
            candidate_notes = []
            if use_last:
                candidate_notes.append(note.Note(token[-1]))
            else:
                for elem in token:
                    candidate_notes.append(note.Note(elem))
            
            for n in candidate_notes:
                yield n.pitch.midi




if __name__ == '__main__':
    embedding = load_model(Path('save/embedding.wv'))
    mixture = BayesianGaussianTypeModel(embedding)
    mixture.load_model(Path('save/mixture.pk'))
    hmm = load_model(Path('save/hmm.pk'))

    types, _ = hmm.sample(5)
    types = types.flatten()
    print('Sampled', types)

    tokens = to_token(types, mixture, embedding)
    score = to_score(tokens, melody_texture)
    score.show('musicxml')
