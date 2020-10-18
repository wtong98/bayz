"""
High-level components used for live-coding.

author: William Tong (wlt2115@columbia.edu)
"""

class Band:
    def __init__(self, cycleLength=2):
        self.cycleLength = cycleLength
        self.lines = []

    def connect(self, server):
        self.server = server
    
    def addPlayer(self):
        pass

    def addLine(self, notes, rhythm=[1], instrument='sine'):
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

    