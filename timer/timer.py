import time


class Timer:
    def __init__(self):
        self.start_time = 0
        self.timeout = 0

    def start(self, value):
        self.start_time = time.time()
        self.timeout = value

    def is_expired(self):
        actual = time.time()
        if actual > (self.start_time + self.timeout):
            return 1
        else:
            return 0
