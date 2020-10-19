"""
High-level components used for live-coding.

author: William Tong (wlt2115@columbia.edu)
"""

from pathlib import Path

from bayz.common import BayesianGaussianTypeModel
from bayz.generate import load_model, to_token, to_midi

class Band:
    def __init__(self, cycleLength=2, model_path=Path('save/'), pre_gen=3):
        if type(model_path) == str:
            model_path = Path(model_path)
        self._load_model(model_path)

        self.cycleLength = cycleLength
        self.lines = []

        self.cache = [self._sample() for _ in range(pre_gen)]
        self.cache_idx = 0

        print('all systems loaded, band ready')


    def connect(self, server):
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
        self.cache = []
        self.cache_idx = 0
    
    def add_player(self, rhythm=[1], instrument='sine'):
        if self.cache_idx < len(self.cache):
            notes = self.cache[self.cache_idx]
        else:
            notes = self._sample()
            self.cache.append(notes)
        
        print('sampled notes', notes)
        self.add_line(notes, rhythm=rhythm, instrument=instrument)
        self.cache_idx += 1

    def add_line(self, notes, rhythm=[1], instrument='sine'):
        line = {
            'name': instrument,
            'notes': notes,
            'rhythm': rhythm
        }
        self.lines.append(line)

    def commit(self):
        data = {
            'sound': self.lines,
            'cycleLength': self.cycleLength,
            'deploy': True
        }
        self.server.commit(data)

        # reset for next run
        self.lines = []
        self.cache_idx = 0

    