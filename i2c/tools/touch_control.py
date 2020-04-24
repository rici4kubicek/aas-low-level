import logging
import time
from nightWiring import io
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.I2C as I2C
from array import array


class TouchControl(object):
    TOUCH_RESET_PIN = 203
    TOUCH_CHANGE_PIN = 200
    TOUCH_I2C_ADDRESS = 0x1B

    TOUCH_CHIP_ID = 0x2E

    TOUCH_DETECTION_STATUS_TOUCH_BIT = 0x01

    TOUCH_CMD_CHIP_ID = 0x00
    TOUCH_CMD_DETECTION_STATUS = 0x02
    TOUCH_CMD_KEY_STATUS = 0x03
    TOUCH_CMD_REG_AVEASK0_OFSSET = 0x27
    TOUCH_CMD_MAX_ON_DURATION = 0x37
    TOUCH_CMD_CALIBRATE = 0x38
    TOUCH_CMD_RESET = 0x39

    logger = logging.getLogger(__name__)

    def __init__(self, i2c_bus=None):
        self._key_hit = False
        self._hold_down = False
        self._init_ok = False
        pin_map = array('i', [self.TOUCH_RESET_PIN, self.TOUCH_CHANGE_PIN])
        io.setupGPIO(pin_map, len([self.TOUCH_RESET_PIN, self.TOUCH_CHANGE_PIN]))
        io.pinMode(0, io.OUTPUT)
        io.digitalWrite(0, io.HIGH)
        io.pinMode(1, io.INPUT)
        time.sleep(1)

        if i2c_bus is None:
            self._i2c = I2C.get_i2c_device(self.TOUCH_I2C_ADDRESS)
        else:
            self._i2c = I2C.get_i2c_device(self.TOUCH_I2C_ADDRESS, busnum=i2c_bus)
        # write non-zero value to reset register
        time.sleep(0.5)
        self._i2c.write8(self.TOUCH_CMD_RESET, 0xff)
        time.sleep(0.5)
        chip_id = self._i2c.readU8(self.TOUCH_CMD_CHIP_ID)
        time.sleep(0.5)
        self._i2c.write8(self.TOUCH_CMD_CALIBRATE, 0xff)
        while self._i2c.readU8(self.TOUCH_CMD_DETECTION_STATUS) & 0x80:
            self.logger.debug("init: calibration in progress ...")
        self._i2c.write8(self.TOUCH_CMD_MAX_ON_DURATION, 0x0)
        if chip_id == self.TOUCH_CHIP_ID:
            self._init_ok = True

    def read_state(self):
        if self._init_ok:
            change_state = io.digitalRead(1)
            if not change_state:
                self._key_hit = True
                self._hold_down = True
                self.logger.debug("read_state: log 0")
            else:
                self.logger.debug("read_state: log 1")

    @staticmethod
    def read_active_address(self):
        if self._init_ok:
            if self._key_hit:
                read_status = self._i2c.readU8(self.TOUCH_CMD_DETECTION_STATUS)
                button_number = self._i2c.readU8(self.TOUCH_CMD_KEY_STATUS)
                self._key_hit = False

                # seems to trigger interrupt twice per press .. filter this
                if read_status & self.TOUCH_DETECTION_STATUS_TOUCH_BIT:
                    if button_number == 0:
                        self.logger.error("read_active_address: Read error")
                    return button_number
        return 0

    @staticmethod
    def set_button_group(self, _key, _group):
        if _group < 4:
            _value = self._i2c.readU8(self.TOUCH_CMD_REG_AVEASK0_OFSSET + _key) & 0xfc
            if _value == 0:
                _value = 8 << 2
        elif _group == 0xff:
            _value = 0
            _group = 1
        else:
            return False
        print(_key)
        print(_value)
        self._i2c.write8(self.TOUCH_CMD_REG_AVEASK0_OFSSET + _key, _value | _group)
        return True

    def read_active_key(self):
        if self._init_ok:
            key_address = self.read_active_address(self)
            if key_address:
                self.logger.debug("read_active_key: key_address {}".format(key_address))
                key_value = 0

                i = key_address
                while i > 0:
                    key_value = key_value + 1
                    i = i >> 1

                active_key = key_value & 0xff
                if key_value == 9:
                    self._hold_down = False

                return key_value
        return 0
