#!/usr/bin/python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
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
from tools.touch_control import TouchControl

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


class AasI2C(object):
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
        self.logger = None
        self.mqtt = None
        self.mqtt_ready = False
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
        path = './static/'

        files = os.listdir(path)
        pattern = "*.ttf"
        for font in files:
            if fnmatch.fnmatch(font, pattern):
                self.fonts[font[:-4] + "-" + str(size) + ""] = ImageFont.truetype("" + path + font + "", size)

    def button_pressed_notification(self, _btn):
        msg = {}
        msg["button"] = _btn
        self.mqtt.publish(LL_TOUCH_TOPIC, json.dumps(msg))


def on_display(moqs, obj, msg):
    obj.logger.debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))

        if 'cmd' in data.keys():
            if data["cmd"] == "clear":
                obj.display_command = "clear"
            elif data["cmd"] == "write":
                obj.display_command = "write"
            else:
                obj.display_command = None

        if 'text' in data.keys() and 'font' in data.keys() and 'pos_x' in data.keys() and 'pos_y' in data.keys():
            obj.write_text["text"] = data["text"]
            obj.write_text["font"] = data["font"]
            obj.write_text["pos_x"] = data["pos_x"]
            obj.write_text["pos_y"] = data["pos_y"]
    except json.JSONDecodeError:
        obj.logger.error("MQTT: received msq is not json with expected information")


def on_connect(mqtt_client, obj, flags, rc):
    if rc == 0:
        obj.mqtt_ready = True
        obj.mqtt.subscribe(LL_DISPLAY_TOPIC)
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


def main():
    aas = AasI2C()
    aas.logger = logging.getLogger()
    aas.logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/var/log/low-level-i2c.txt")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    aas.logger.addHandler(fh)
    aas.logger.addHandler(ch)

    aas.logger.info("Core: ===================== Application start ========================")
    aas.logger.info("Script version: {}".format(__version__))

    aas.mqtt = mqtt.Client()
    aas.mqtt.connect("localhost")
    aas.mqtt.publish(LL_I2C_MSG_TOPIC, "I2C: prepared")
    aas.mqtt.on_connect = on_connect
    aas.mqtt.user_data_set(aas)
    aas.mqtt.message_callback_add(LL_DISPLAY_TOPIC, on_display)

    aas.display_begin()

    if not aas.display_ready:
        aas.mqtt.publish(LL_I2C_MSG_TOPIC, "I2C: display is not ready")

    aas.load_fonts(10)
    aas.load_fonts(12)
    aas.load_fonts(15)

    cmd = "hostname -I | cut -d\' \' -f1"
    ip = subprocess.check_output(cmd, shell=True)
    txt = "IP: " + str(ip, "ascii") + ""

    aas.clear_display()
    aas.image = Image.open('static/vut_logo_left_name.png').convert('1').resize((128, 32), Image.ANTIALIAS)
    aas.draw = ImageDraw.Draw(aas.image)
    aas.draw.text((32, 22), txt, font=aas.fonts["Arial-10"], fill=255)
    aas.display.image(aas.image)
    aas.send_to_display()

    aas.mqtt.loop_start()

    while 1:
        key = aas.touch.read_active_key()
        if key:
            aas.button_pressed_notification(key)

        if aas.display_command == "clear":
            aas.clear_display()
            aas.clear_display_buffer()
        elif aas.display_command == "write":
            aas.draw.text((aas.write_text["pos_x"], aas.write_text["pos_y"]), aas.write_text["text"],
                          font=aas.fonts[aas.write_text["font"]], fill=255)
            aas.display.image(aas.image)
            aas.send_to_display()
            aas.clear_display_buffer()

        if not aas.display_ready:
            aas.display_begin()

        aas.touch.wait_events(0.01)


def touch_handle():
    touch = TouchControl(i2c_bus="0")

    while 1:
        key = touch.read_active_key()
        if key:
            print(key)
        touch.wait_events()


if __name__ == "__main__":
    main()

