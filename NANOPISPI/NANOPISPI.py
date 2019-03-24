import spidev
from nightWiring import io
from array import array
import threading


class NANOPISPI:

    def __init__(self):
        io.setup()
        self.mutex = threading.Lock()

    def open(self, spi_bus, spi_device, max_speed_hz):
        '''
        Open SPI bus
        :param spi_bus:
        :param spi_device:
        :param max_speed_hz:
        :return:
        '''
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = max_speed_hz
        # self.spi.no_cs = True

    def cs_init(self, cs_pins):
        '''
        Initiate CS pins as outputs
        :param cs_pins: array of pin numbers
        '''
        pin_map = array('i', cs_pins)
        io.setupGPIO(pin_map, len(cs_pins))
        idx = 0
        while idx < len(cs_pins):
            io.pinMode(idx, io.OUTPUT)
            idx = idx + 1

    def cs_set(self, cs_pin_idx, value):
        '''
        Set value on CS pin
        :param cs_pin_idx: index of CS pin from cs_pins placed in cs_init
        :param value: 1 or 0
        :return:
        '''
        if value == 1:
            io.digitalWrite(cs_pin_idx, io.HIGH)
        if value == 0:
            io.digitalWrite(cs_pin_idx, io.LOW)

    def write(self, data):
        self.mutex.acquire()
        self.spi.xfer(data)
        self.mutex.release()

    def read_byte(self, cmd):
        self.mutex.acquire()
        val = self.spi.xfer(cmd)
        self.mutex.release()
        return val[1]