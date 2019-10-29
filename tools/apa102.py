from tools import *
import logging

# create logger
module_logger = logging.getLogger('apa102')


class APA102(object):
    def __init__(self, led_count):
        self._logger = logging.getLogger('apa102')
        self._led_count = led_count
        self._led_array = [0, 0, 0, 0]
        i = 0
        while i < self._led_count:
            self._led_array.append([0])
            self._led_array.append([0])
            self._led_array.append([0])
            self._led_array.append([0])
            i = i + 1
        self._led_array.append(0xff)
        self._led_array.append(0xff)
        self._led_array.append(0xff)
        self._led_array.append(0xff)

    def prepare_data(self, r, g, b, brightness, led_idx):
        _brightness = valmap(brightness, 0, 100, 0, 31)
        self._led_array[led_idx * 4 + 4] = 0xe0 + _brightness
        r = valmap(r, 0, 255, 0, 255)
        g = valmap(g, 0, 255, 0, 255)
        b = valmap(b, 0, 255, 0, 255)
        self._led_array[led_idx * 4 + 5] = b
        self._led_array[led_idx * 4 + 6] = g
        self._led_array[led_idx * 4 + 7] = r

    def get_data(self):
        return self._led_array
