"""
Trains a BPL model to generate music

author: William Tong (wlt2115@columbia.edu)
"""
import pickle
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from gensim.models import Word2Vec
from gensim.models import KeyedVectors

from hmmlearn import hmm

from music21 import corpus
from music21 import interval
from music21 import note

from sklearn.mixture import BayesianGaussianMixture

from tqdm import tqdm


save_path = Path('save/')
corpus_path = save_path / 'corpus.pk'
embedding_path = save_path / 'embedding.wv'
mixture_path = save_path / 'mixture.pk'
plot_path = save_path / 'plot.png'

hmm_path = save_path / 'hmm.pk'

def fetch_texts(cache=True) -> list:
    texts = None
    if corpus_path.exists() and cache:
        with corpus_path.open('rb') as fp:
            texts = pickle.load(fp)
    else:
        bach_bundle = corpus.search('bach', 'composer')
        scores = [metadata.parse() for metadata in bach_bundle]
        texts = list(tqdm(convert_to_texts(scores), total=len(scores)))
        
        if cache:
            with corpus_path.open('wb') as fp:
                pickle.dump(texts, fp)
        
    return texts


def convert_to_texts(scores, sampling_rate=0.5):
    for score in scores:
        normalized_score = _transpose(score)
        text = _to_text(normalized_score, sampling_rate)
        yield text


def _transpose(score, target=note.Note('c')) -> 'Score':
    ky = score.analyze('key')
    home = note.Note(ky.tonicPitchNameWithCase)
    intv = interval.Interval(home, target)

    return score.transpose(intv)


def _to_text(score, sampling_rate) -> list:
    notes = score.flat.getElementsByClass(note.Note)
    hist = _bin(notes, sampling_rate)
    end = score.flat.highestOffset

    text = [_to_word(hist[i]) for i in np.arange(0, end, sampling_rate)]
    return text


def _bin(notes, sampling_rate) -> defaultdict:
    hist = defaultdict(list)

    for note in notes:
        offset = note.offset
        halt = offset + note.duration.quarterLength

        if _precise_round(offset % sampling_rate) != 0:
            offset = _precise_round(offset - (offset % sampling_rate))
        if _precise_round(halt % sampling_rate) != 0:
            halt = _precise_round(halt + (sampling_rate - halt % sampling_rate))

        while offset < halt:
            hist[offset].append(note)
            offset += sampling_rate

    return hist


def _to_word(notes, rest_word="REST") -> str:
    if len(notes) == 0:
        return rest_word

    ordered_notes = sorted(notes, key=lambda n: n.pitch.midi, reverse=True)
    word = ''.join([note.name for note in ordered_notes])
    return word


def _precise_round(val, precision=10):
    return round(val * precision) / precision


def train_wv_model(texts, save=True) -> 'Word2Vec':
    model = Word2Vec(sentences=texts,
                     size=32,
                     min_count=1,
                     window=4,
                     workers=4,
                     sg=1)
    if save:
        model.wv.save(str(embedding_path))
    
    return model

def fit_mixture(points, save=True, plot=True):
    mixture = BayesianGaussianMixture(n_components=32)
    mixture.fit(points)

    labels = mixture.predict(points)
    if plot:
        plt.hist(labels, bins=32)
        plt.savefig(plot_path)
    
    if save:
        with mixture_path.open('wb') as fp:
            pickle.dump(mixture, fp)

    return labels


def texts_to_seqs(texts, wv, labels) -> list:
    word_to_label = {}
    vocab = wv.vocab
    for word in vocab:

        idx = vocab[word].index
        word_to_label[word] = labels[idx]

    def _text_to_seq(text):
        return np.array([[word_to_label[word]] for word in text])

    sequences = [_text_to_seq(text) for text in texts]
    return sequences


def train_hmm(sequences, save=True):
    type_gen_model = hmm.MultinomialHMM(n_components=16)
    lengths = [len(seq) for seq in sequences]
    sequences = np.concatenate(sequences)
    type_gen_model.fit(sequences, lengths=lengths)

    if save:
        with hmm_path.open('wb') as pickle_f: 
            pickle.dump(type_gen_model, pickle_f)
    
    return type_gen_model


if __name__ == '__main__':
    if not save_path.exists():
        save_path.mkdir()
    
    print('fetching corpus')
    texts = fetch_texts()

    print('training word2vec model')
    wv = train_wv_model(texts).wv

    print('fitting mixture model')
    labels = fit_mixture(wv.vectors)

    print('training hmm')
    sequences = texts_to_seqs(texts, wv, labels)
    hmm = train_hmm(sequences)
    print('fitted weight matrix', hmm.transmat_)
    print('done!')
