import json
from collections import deque

class DeviceBuffer:
    def __init__(self, maxlen=20):
        self.seq = 0
        self.deque = deque(maxlen=maxlen)
        # self.long_deque = deque(maxlen=1000)

    def add_data(self, data):
        self.deque.append((self.seq, data))
        # self.long_deque.append((self.seq, data))
        # if len(self.long_deque) == 100:
        #     with open("long_deque.json", "w") as f:
        #         f.write(json.dumps(tuple(self.long_deque)))
        self.seq += 1

    def json(self):
        return json.dumps(tuple(self.deque))
    
    def jsonable(self):
        return tuple(self.deque)