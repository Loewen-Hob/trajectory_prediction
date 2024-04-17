import time


class Timer:
    def __init__(self, lvl=0):
        self.last_time = time.time()
        self._lvl = lvl

    def get_spend_time(self, s:str, threshold=0.01):
        t = time.time()
        dt = t - self.last_time
        if dt > threshold:
            print(self._lvl * 4 * '-', s, dt)
        self.last_time = t