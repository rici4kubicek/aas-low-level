class APA102(object):
    def __init__(self, led_count):
        self.led_count = led_count
        self.led_array = [0, 0, 0, 0]
        i = 0
        while i < led_count:
            self.led_array.append([0])
            self.led_array.append([0])
            self.led_array.append([0])
            self.led_array.append([0])
            i = i + 1
        self.led_array.append(0xff)
        self.led_array.append(0xff)
        self.led_array.append(0xff)
        self.led_array.append(0xff)

    def prepare_data(self, r, g, b, brightness, led_idx):
        if brightness > 32:
            brightness = 31
        self.led_array[led_idx * 4 + 4] = 0xe0 + brightness
        self.led_array[led_idx * 4 + 5] = b
        self.led_array[led_idx * 4 + 6] = g
        self.led_array[led_idx * 4 + 7] = r

    def get_data(self):
        return self.led_array
