#!/usr/bin/python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt_client
import json
import os
import fnmatch
import time
import subprocess
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
from app.touch_control import TouchControl
from app.nanopi_spi import NanoPiSpi
from app.apa102 import APA102
from app.mfrc522 import MFRC522

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.1.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"

LL_I2C_TOPIC = "i2c"
LL_DISPLAY_TOPIC = LL_I2C_TOPIC + "/display"
LL_I2C_MSG_TOPIC = LL_I2C_TOPIC + "/msg"
LL_TOUCH_TOPIC = LL_I2C_TOPIC + "/touch"
LL_SPI_TOPIC = "spi"
LL_READER_TOPIC = LL_SPI_TOPIC + "/reader"
LL_READER_DATA_TOPIC = LL_READER_TOPIC + "/data"
LL_READER_DATA_READ_TOPIC = LL_READER_TOPIC + "/data/read"
LL_READER_DATA_WRITE_TOPIC = LL_READER_TOPIC + "/data/write"
LL_READER_STATUS_TOPIC = LL_READER_TOPIC + "/state"
LL_SPI_MSG_TOPIC = LL_SPI_TOPIC + "/msg"
LL_LED_TOPIC = LL_SPI_TOPIC + "/led"


class Aas:
    _mqtt = mqtt_client.Client()
    _logger = logging.getLogger()

    def __init__(self):
        self.i2c = AasI2C()
        self.spi = AasSpi()
        self.mqtt_ready = False

    def publish(self, topic, data):
        self._mqtt.publish(topic, data)

    def mqtt(self):
        return self._mqtt

    def logger(self):
        return self._logger

    def logger_debug(self, _str):
        self._logger.debug(_str)

    def logger_error(self, _str):
        self._logger.error(_str)


class AasI2C(Aas):
    def __init__(self):
        self.display = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus='0')
        self._width = self.display.width
        self._height = self.display.height
        self.image = Image.new('1', (self._width, self._height))
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)
        self.fonts = {}
        self.write_text = {}
        self.display_command = None
        self.display_ready = False
        self.touch = TouchControl(i2c_bus="0")

    def display_begin(self):
        try:
            self.display.begin()
            self.display.clear()
            self.display.display()
            self.display_ready = True
        except:
            self.display_ready = False

    def send_to_display(self):
        if self.display_ready:
            self.display.display()

    def clear_display_buffer(self):
        self.display_command = ""

    def clear_display(self):
        if self.display_ready:
            self.display.clear()
            self.draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)
            self.display.display()
            self.clear_display_buffer()

    def load_fonts(self, size):
        path = 'static/'

        files = os.listdir(path)
        pattern = "*.ttf"
        for font in files:
            if fnmatch.fnmatch(font, pattern):
                self.fonts[font[:-4] + "-" + str(size) + ""] = ImageFont.truetype("" + path + font + "", size)

    def button_pressed_notification(self, _btn):
        msg = {}
        msg["button"] = _btn
        super().publish(LL_TOUCH_TOPIC, json.dumps(msg))

    def init_screen(self):
        cmd = "hostname -I | cut -d\' \' -f1"
        ip = subprocess.check_output(cmd, shell=True)
        txt = "IP: " + str(ip, "ascii") + ""

        self.clear_display()
        self.image = Image.open('static/vut_logo_left_name.png').convert('1').resize((128, 32), Image.ANTIALIAS)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.text((32, 22), txt, font=self.fonts["Arial-10"], fill=255)
        self.display.image(self.image)
        self.send_to_display()

    def display_loop(self):
        if self.display_command == "clear":
            self.clear_display()
            self.clear_display_buffer()
        elif self.display_command == "write":
            self.draw.text((self.write_text["pos_x"], self.write_text["pos_y"]), self.write_text["text"],
                           font=self.fonts[self.write_text["font"]], fill=255)
            self.display.image(self.image)
            self.send_to_display()
            self.clear_display_buffer()

        if not self.display_ready:
            self.display_begin()


class AasSpi(Aas):
    def __init__(self):
        self.nano_pi = NanoPiSpi()
        self.led = APA102(4)
        self.send_led = False
        self.write_data = {}
        self.write_data_flag = False
        self.write_multi_data_flag = False
        self.old_read_data = []

        self.nano_pi.led_cs_init()
        self.nano_pi.led_cs_set(1)
        self.nano_pi.open(0, 0, 2000000)

        self.led.prepare_data(0, 0, 0, 0, 0)
        self.led.prepare_data(0, 0, 0, 0, 1)
        self.led.prepare_data(0, 0, 0, 0, 2)
        self.led.prepare_data(0, 0, 0, 0, 3)

        self.nano_pi.led_cs_init()
        self.nano_pi.led_cs_set(1)
        self.nano_pi.write(self.led.get_data())
        self.nano_pi.led_cs_set(0)

        self.nano_pi.reader_reset_init()
        self.nano_pi.reader_reset_set(1)

        self.mifare_reader = MFRC522(self.nano_pi)

    def reader_loop(self):
        card_data = {}
        # Scan for cards
        (status, TagType) = self.mifare_reader.request(self.mifare_reader.PICC_REQIDL)

        # If a card is found
        if status == self.mifare_reader.MI_OK:
            super().publish(LL_READER_TOPIC, "Some card detected")
            super().logger_debug("CARD: card detected")
            card_data["timestamp"] = time.time()

        # Get the UID of the card
        (status, uid) = self.mifare_reader.anticoll(1)

        # If we have the UID, continue
        if status == self.mifare_reader.MI_OK:
            if not self.write_data_flag and not self.write_multi_data_flag:
                super().logger_debug(
                    "Card read UID: {}, {}, {}, {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]), hex(uid[3])))
                self.mifare_reader.select_tag(uid)
                card_data["data"], state = self.mifare_reader.dump_ultralight(uid)
                # properly parse UID from readed data
                card_data["uid"] = self.mifare_reader.parse_serial_number(card_data["data"])
                if state == self.mifare_reader.MI_OK:
                    card_data["read_state"] = "OK"
                else:
                    card_data["read_state"] = "ERROR"
                data = self.mifare_reader.get_version()
                card_data["tag"] = tag_parse_version(data)
                if self.old_read_data != card_data["data"]:
                    super().publish(LL_READER_DATA_READ_TOPIC, json.dumps(card_data))
                self.old_read_data = card_data["data"]
            elif self.write_data_flag:
                #write_to_tag(uid, self.mifare_reader, aas)
                pass
            elif self.write_multi_data_flag:
                super().logger_debug("Write multi data")
                #write_multi_to_tag(uid, mifare_reader, aas)
                pass

            self.mifare_reader.stop_crypto1()
            (status, TagType) = self.mifare_reader.request(self.mifare_reader.PICC_HALT)
        else:
            self.old_read_data = []

    def led_loop(self):
        if self.send_led:
            self.nano_pi.led_cs_set(1)
            self.nano_pi.write(self.led.get_data())
            self.nano_pi.led_cs_set(0)
            self.send_led = False


def on_leds(moqs, obj, msg):
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        obj.spi.led.prepare_data(data["led_0"]["red"], data["led_0"]["green"], data["led_0"]["blue"],
                                 data["led_0"]["brightness"], 0)
        obj.spi.led.prepare_data(data["led_1"]["red"], data["led_1"]["green"], data["led_1"]["blue"],
                                 data["led_1"]["brightness"], 1)
        obj.spi.led.prepare_data(data["led_2"]["red"], data["led_2"]["green"], data["led_2"]["blue"],
                                 data["led_2"]["brightness"], 2)
        obj.spi.led.prepare_data(data["led_3"]["red"], data["led_3"]["green"], data["led_3"]["blue"],
                                 data["led_3"]["brightness"], 3)
        obj.spi.send_led = True
    except json.JSONDecodeError:
        obj.logger_error("MQTT: received msq is not json with expected information")


def on_write(moqs, obj, msg):
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        if "write" in data:
            obj.spi.write_data["sector"] = data["write"][0]["sector"]
            obj.spi.write_data["data"] = data["write"][0]["data"]
            obj.logger.debug(obj.spi.write_data)
            obj.spi.write_data_flag = True
            obj.spi.write_multi_data_flag = False
            obj.spi.count_of_pages_to_write = len(data["write"])
        elif "write_multi" in data:
            print(data["write_multi"])
            obj.spi.write_data["write_multi"] = data["write_multi"]
            obj.logger.debug(obj.spi.write_data)
            obj.spi.write_data_flag = False
            obj.spi.write_multi_data_flag = True
            obj.spi.count_of_pages_to_write = len(data["write_multi"])
    except json.JSONDecodeError:
        obj.logger_error("MQTT: received msq is not json with expected information")


def on_display(moqs, obj, msg):
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))

        if 'cmd' in data.keys():
            if data["cmd"] == "clear":
                obj.i2c.display_command = "clear"
            elif data["cmd"] == "write":
                obj.i2c.display_command = "write"
            else:
                obj.i2c.display_command = None

        if 'text' in data.keys() and 'font' in data.keys() and 'pos_x' in data.keys() and 'pos_y' in data.keys():
            obj.i2c.write_text["text"] = data["text"]
            obj.i2c.write_text["font"] = data["font"]
            obj.i2c.write_text["pos_x"] = data["pos_x"]
            obj.i2c.write_text["pos_y"] = data["pos_y"]
    except json.JSONDecodeError:
        obj.logger_error("MQTT: received msq is not json with expected information")


def on_connect(mqtt_client, obj, flags, rc):
    if rc == 0:
        obj.mqtt_ready = True
        obj.mqtt().subscribe(LL_DISPLAY_TOPIC)
        obj.mqtt().subscribe(LL_LED_TOPIC)
        obj.mqtt().subscribe(LL_READER_DATA_WRITE_TOPIC)
    else:
        obj.mqtt_ready = 0
        retry_time = 2
        while rc != 0:
            time.sleep(retry_time)
            try:
                rc = mqtt_client.reconnect()
            except Exception as e:
                rc = 1
                retry_time = 5


def _tag_type_string(storage_size):
    if storage_size == 0x0f:
        return "NTAG213"
    elif storage_size == 0x11:
        return "NTAG215"
    elif storage_size == 0x13:
        return "NTAG216"
    else:
        return "Unknown"


def _tag_memory_size(storage_size):
    if storage_size == 0x0f:
        return 144
    elif storage_size == 0x11:
        return 504
    elif storage_size == 0x13:
        return 888
    else:
        return 0


def _tag_vendor_to_string(vendor_id):
    if vendor_id == 4:
        return "NXP"
    else:
        return "Unknown"


def _tag_user_memory_offset(data):
    return 4


def tag_parse_version(data):
    back_data = {"tag_size": _tag_memory_size(data["storage_size"]), "tag_type": _tag_type_string(data["storage_size"]),
                 "tag_vendor": _tag_vendor_to_string(data["vendor_id"]), "tag_protocol": data["protocol_type"],
                 "user_memory_offset": _tag_user_memory_offset(data)}
    return back_data


def publish_write_status(aas, status, sector, _mqtt):
    data = {"write": {"sector": 0, "status": "NONE"}}
    data["write"]["sector"] = sector
    data["write"]["status"] = status
    _mqtt.publish(LL_READER_STATUS_TOPIC, json.dumps(data))


def write_to_tag(uid, reader, aas):
    uid[0] = uid[1]
    uid[1] = uid[2]
    uid[2] = uid[3]

    SAK1 = reader.sak(uid)

    (Status, uid2) = reader.anticoll(2)
    uid[3] = uid2[0]
    uid[4] = uid2[1]
    uid.append(uid2[2])
    uid.append(uid2[3])
    reader.select_tag2(uid)
    aas.logger.debug(
        "Card UID: {}, {}, {}, {} write data to sector".format(hex(uid[0]), hex(uid[1]), hex(uid[2]),
                                                               hex(uid[3]), aas.write_data["sector"]))
    status = reader.write(aas.write_data["sector"], aas.write_data["data"])
    if status == reader.MI_OK:
        publish_write_status(aas, "OK", aas.write_data["sector"], aas.mqtt)
        aas.write_data_flag = False
    else:
        publish_write_status(aas, "NOK", aas.write_data["sector"], aas.mqtt)


def write_multi_to_tag(uid, reader, aas):
    uid[0] = uid[1]
    uid[1] = uid[2]
    uid[2] = uid[3]

    SAK1 = reader.sak(uid)

    (Status, uid2) = reader.anticoll(2)
    uid[3] = uid2[0]
    uid[4] = uid2[1]
    uid.append(uid2[2])
    uid.append(uid2[3])
    reader.select_tag2(uid)
    aas.logger.debug(
        "Card UID: {}, {}, {}, {} write multi data to sectors {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]),
                                                                         hex(uid[3]), aas.write_data["write_multi"]))
    i = 0
    while i < aas.count_of_pages_to_write:
        status = reader.write(aas.write_data["write_multi"][i]["sector"], aas.write_data["write_multi"][i]["data"])
        if status == reader.MI_OK:
            publish_write_status(aas, "OK", aas.write_data["write_multi"][i]["sector"], aas.mqtt)
            i = i + 1
        else:
            publish_write_status(aas, "NOK", aas.write_data["write_multi"][i]["sector"], aas.mqtt)

    if i == aas.count_of_pages_to_write:
        aas.write_multi_data_flag = False


def main():
    aas = Aas()
    aas.logger().setLevel(logging.DEBUG)
    fh = logging.FileHandler("/var/log/aas-low-level.txt")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    aas.logger().addHandler(fh)
    aas.logger().addHandler(ch)

    aas.logger().info("Core: ===================== Application start ========================")
    aas.logger().info("Script version: {}".format(__version__))

    aas.mqtt().connect("localhost")
    aas.mqtt().publish(LL_I2C_MSG_TOPIC, "I2C: prepared")
    aas.mqtt().on_connect = on_connect
    aas.mqtt().user_data_set(aas)
    aas.mqtt().message_callback_add(LL_DISPLAY_TOPIC, on_display)
    aas.mqtt().message_callback_add(LL_LED_TOPIC, on_leds)
    aas.mqtt().message_callback_add(LL_READER_DATA_WRITE_TOPIC, on_write)

    aas.i2c.display_begin()

    if not aas.i2c.display_ready:
        aas.mqtt().publish(LL_I2C_MSG_TOPIC, "I2C: display is not ready")

    aas.i2c.load_fonts(10)
    aas.i2c.load_fonts(12)
    aas.i2c.load_fonts(15)

    aas.i2c.init_screen()

    aas.mqtt().loop_start()

    while True:
        key = aas.i2c.touch.read_active_key()
        if key:
            aas.i2c.button_pressed_notification(key)

        aas.i2c.display_loop()

        aas.spi.reader_loop()

        aas.spi.led_loop()

        aas.i2c.touch.wait_events(0.01)


def touch_handle():
    touch = TouchControl(i2c_bus="0")

    while 1:
        key = touch.read_active_key()
        if key:
            print(key)
        touch.wait_events()


if __name__ == "__main__":
    main()
