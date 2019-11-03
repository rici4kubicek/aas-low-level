import spidev
import threading
import gpio


class NanoPiSpi(object):

    LED_CS_PIN = 6
    READER_RST_PIN = 7
    READER_CS_PIN = 67

    def __init__(self):
        gpio.Controller.available_pins = gpio.Controller.available_pins
        self.mutex = threading.Lock()
        self.spi = None
        self.led_cs = None
        self.reader_rst = None
        self.reader_cs = None

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
        gpio.Controller.available_pins = gpio.Controller.available_pins + [NanoPiSpi.LED_CS_PIN]
        self.led_cs = gpio.Controller.alloc_pin(NanoPiSpi.LED_CS_PIN, gpio.OUTPUT)

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
        gpio.Controller.available_pins = gpio.Controller.available_pins + [NanoPiSpi.READER_RST_PIN]
        self.reader_rst = gpio.Controller.alloc_pin(NanoPiSpi.READER_RST_PIN, gpio.OUTPUT)

    def reader_reset_set(self, value):
        if value == 1:
            self.reader_rst.set()
        if value == 0:
            self.reader_rst.reset()

    def reader_cs_init(self):
        """
        Initiate reader CS pin as output
        """
        gpio.Controller.available_pins = gpio.Controller.available_pins + [NanoPiSpi.READER_CS_PIN]
        self.reader_cs = gpio.Controller.alloc_pin(NanoPiSpi.READER_CS_PIN, gpio.OUTPUT)

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