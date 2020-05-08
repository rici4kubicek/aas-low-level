import spidev
import threading
from app.gpio import Controller, OUTPUT
from array import array


class NanoPiSpi(object):

    LED_CS_PIN = 6
    READER_RST_PIN_1 = 7
    READER_RST_PIN_2 = 363
    READER_CS_PIN = 67

    def __init__(self):
        Controller.available_pins = [self.LED_CS_PIN] + Controller.available_pins
        Controller.available_pins = [self.READER_RST_PIN_1, self.READER_RST_PIN_2] + Controller.available_pins
        Controller.available_pins = [self.READER_CS_PIN] + Controller.available_pins
        self.mutex = threading.Lock()
        self.spi = None
        self.led_cs = Controller.alloc_pin(self.LED_CS_PIN, OUTPUT)
        self.reader_rst = Controller.alloc_pin(self.READER_RST_PIN_1, OUTPUT)
        self.reader_rst_2 = Controller.alloc_pin(self.READER_RST_PIN_2, OUTPUT)
        #self.reader_cs = Controller.alloc_pin(self.READER_CS_PIN, OUTPUT)

    def open(self, spi_bus, spi_device, max_speed_hz):
        """ Open SPI bus
        :param spi_bus:
        :param spi_device:
        :param max_speed_hz:
        :return:
        """
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = max_speed_hz
        # self.spi.no_cs = True

    def led_cs_init(self):
        """
        Initiate LED CS pin as output
        """
        pass

    def led_cs_set(self, value):
        """
        Set value on CS pin
        :param cs_pin_idx: index of CS pin from cs_pins placed in cs_init
        :param value: 1 or 0
        :return:
        """
        if value == 1:
            self.led_cs.set()
        if value == 0:
            self.led_cs.reset()

    def reader_reset_init(self):
        """
        Initiate reader reset pin as output
        :return:
        """
        pass

    def reader_reset_set(self, value):
        """
        Set value on RST pin
        :param value:
        :return:
        """
        if value == 1:
            self.reader_rst.set()
            self.reader_rst_2.set()
        if value == 0:
            self.reader_rst.reset()
            self.reader_rst_2.reset()

    def reader_cs_init(self):
        """
        Initiate reader CS pin as output
        """
        pass

    def reader_cs_set(self, value):
        """
        Set value on CS pin
        :param cs_pin_idx: index of CS pin from cs_pins placed in cs_init
        :param value: 1 or 0
        :return:
        """
        if value == 1:
            self.reader_cs.set()
        if value == 0:
            self.reader_cs.reset()

    def write(self, data):
        self.mutex.acquire()
        if self.spi:
            self.spi.xfer(data)
        else:
            raise Exception("SPI bus is not opened! Open bus before you try to write on bus")
        self.mutex.release()

    def read_byte(self, cmd):
        val = [None, None]
        self.mutex.acquire()
        if self.spi:
            val = self.spi.xfer(cmd)
        else:
            raise Exception("SPI bus is not opened! Open bus before you try read from bus")
        self.mutex.release()
        return val[1]