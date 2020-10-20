"""
High-level components used for live-coding. It's recommended to use a 
jupyter notebook as your live-coding platform. See live.py or live.ipynb
for an example environment. If you plan to use machine learning additions,
remember to have saved models in your current working directory. To train
a BPL model, do

$ python -m bayz.train

and a set of model files will be saved to 'save/'

author: William Tong (wlt2115@columbia.edu)
"""

from pathlib import Path

from bayz.common import BayesianGaussianTypeModel
from bayz.generate import load_model, to_token, to_midi

class Band:
    def __init__(self, cycleLength=2, model_path=Path('save/'), pre_gen=3):
        """
        param cycleLength: duration of a cycle, in seconds. One cycle
                           corresponds to one loop through a line of notes.
        param model_path: location of saved model files
        param pre_gen: number of sampled music sequences to cache on start-up
        """

        if type(model_path) == str:
            model_path = Path(model_path)

        print('starting band...')
        self._load_model(model_path)

        self.cycleLength = cycleLength
        self.lines = []

        self.cache = [self._sample() for _ in range(pre_gen)]
        self.cache_idx = 0

        print('all systems loaded, band ready')


    def connect(self, server):
        """
        Connects the band to a bayz server instance.

        param server: bayz server object
        """

        self.server = server

    
    def _load_model(self, model_path: Path):
        self.embedding = load_model(model_path / 'embedding.wv')
        self.mixture = BayesianGaussianTypeModel(self.embedding)
        self.mixture.load_model(model_path / 'mixture.pk')
        self.hmm = load_model(model_path / 'hmm.pk')
    

    def _sample(self) -> 'list':
        types, _ = self.hmm.sample(1)
        types = types.flatten()
        tokens = to_token(types, self.mixture, self.embedding)
        notes = list(to_midi(tokens))

        return notes

    
    def hard_refresh(self):
        """
        Clears the cache of generated music samples
        """

        self.cache = []
        self.cache_idx = 0


    def add_line(self, notes, rhythm=[1], instrument='sine'):
        """
        Adds a new line of music to be played. The rhythm system allows users to
        specify relative durations per notes. When being rendered, notes are
        assigned actual durations in proportion to their rhythm assignment, and
        such that they sum to the cycleLength. A note at index i is assigned
        a rhythm at index i % len(rhythm).

        param notes: note values to be performed (specified as midi values)
        param rhythm: relative duration of notes
        param instrument: instrument that the notes should be played with.
                          Current options are "sine," "bell," and "warble."
        """

        line = {
            'name': instrument,
            'notes': notes,
            'rhythm': rhythm
        }
        self.lines.append(line)

    
    def add_player(self, rhythm=[1], instrument='sine'):
        """
        Produces a line of music in the style of add_line, but no notes are
        specified. Instead, a sequence of samples is sampled from the BPL
        model.

        param rhythm: relative duration of notes
        param instrument: instrument that the notes should be played with
        """

        if self.cache_idx < len(self.cache):
            notes = self.cache[self.cache_idx]
        else:
            notes = self._sample()
            self.cache.append(notes)
        
        print('sampled notes', notes)
        self.add_line(notes, rhythm=rhythm, instrument=instrument)
        self.cache_idx += 1


    def commit(self):
        """
        Commits the music data to the server. After committing, all music
        data is refreshed. Sampled music in the cache will be reduplicated,
        allowing it to persist across live code runs.
        """

        data = {
            'sound': self.lines,
            'cycleLength': self.cycleLength,
            'deploy': True
        }
        self.server.commit(data)

        # reset for next run
        self.lines = []
        self.cache_idx = 0
