"""
Common files and values used across bayz. As of now, it is home only to the
BayesianGaussianTypeModel. Much of this class has been adapted from
https://github.com/wtong98/4772-Project, which was mostly authored by
@huberf. The comments are my own.

author: William Tong (wlt2115@columbia.edu)
"""

import os.path
import pickle
import random

from collections import defaultdict, Counter

import numpy as np
from sklearn.mixture import BayesianGaussianMixture
import scipy.stats

class BayesianGaussianTypeModel:
    """
    Convenience class that wraps an underlying Gaussian mixture model with
    additional project-relevant sampling procedures and calculation
    """

    def __init__(self, embedding, n_components=32, smooth: int = 0.01, do_conditional: bool = True):
        """
        param embedding: gensim.Word2Vec model
        param n_components: number of mixtures to fit. Not an exact number -- it
                            will be tuned by the algorithm
        param smooth: smoothing factor for unseen n-grams
        param do_conditional: whether to apply conditional calculations when
                              sampling
        """

        self.embedding = embedding
        self.n_grams = [2, 3] # set up for 2 and 3-gram combo
        self.do_conditional = do_conditional
        self.smooth = smooth
        self.n = n_components

        # Set up function caching
        self.norm_prob_cache = {}

    def fit(self, scores):
        """
        Fits a mixture model to the provided embedding, and generates n-gram
        probabilities for the associated scores

        param scores: scores for which to generate n-gram probabilities
        """

        self.mixture = BayesianGaussianMixture(n_components=self.n)
        self.mixture.fit(self.embedding.wv.vectors)
        # Fit conditional dependence model
        # Compute n-gram model
        gram_map = { 2: defaultdict(Counter), 3: defaultdict(Counter) }
        for score in scores:
            for n_gram in self.n_grams:
                for i in range(len(score)-n_gram+1):
                    followed = score[i+n_gram-1]
                    gram = tuple(score[i:i+n_gram-1])
                    gram_map[n_gram][gram][followed] += 1
        self.gram_map = gram_map


    def predict(self, vector):
        """
        Returns the id of the mixture that vector most likely belongs to
        """

        return self.mixture.predict(vector)

    def conditional_prob(self, option, prev_words):
        """
        Calculates the probabilities of an n-gram
        """

        smooth_count = 0
        for n_gram in self.n_grams:
            prev_key = tuple(prev_words[-(n_gram-1):])
            followers = self.gram_map[n_gram][prev_key]
            smooth_count += followers[option] + self.smooth #*((n_gram-1)**2) + self.smooth
        return smooth_count

    def emit(self, type_id, prev_words=[]):
        """
        Samples a new token for the given mixture id based in previously
        observed tokens
        """

        mean = self.mixture.means_[type_id,:]
        cov = self.mixture.covariances_[type_id,:,:]
        if len(prev_words) == [] or not self.do_conditional: # if not conditioning on previous
            draw = np.random.multivariate_normal(mean, cov)
        else:
            opts = list(self.embedding.vocab)
            weights = []
            if not type_id in self.norm_prob_cache:
                self.norm_prob_cache[type_id] = [scipy.stats.multivariate_normal(mean, cov).pdf(self.embedding[wrd]) for \
                              wrd in opts]
            for i, wrd in enumerate(opts):
                norm_prob = self.norm_prob_cache[type_id][i]
                ngram_prob = self.conditional_prob(wrd, prev_words)
                weights.append(norm_prob*ngram_prob)
            draw = random.choices(population=opts, k=1, weights=weights)[0]
            print(draw, type_id)
            # convert to vector for legacy support
            draw = self.embedding[draw]
        return draw

    def save_model(self, file_name):
        """
        Pickles the model parameters
        """

        s = pickle.dumps({ 'mixture': self.mixture, 'gram_map': self.gram_map })
        open(file_name, 'wb').write(s)

    def load_model(self, file_name):
        """
        Reloads the model parameters
        """

        s = open(file_name, 'rb').read()
        data = pickle.loads(s)
        self.mixture = data['mixture']
        self.gram_map = data['gram_map']
