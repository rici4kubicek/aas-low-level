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

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"

LL_I2C_TOPIC = "i2c"
LL_DISPLAY_TOPIC = LL_I2C_TOPIC + "/display"
LL_I2C_MSG_TOPIC = LL_I2C_TOPIC + "/msg"


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


def on_display(moqs, obj, msg):
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
    except:
        pass


def on_connect(mqtt_client, obj, flags, rc):
    global mqtt_ready
    if rc==0:
        mqtt_ready = 1
        mqttc.subscribe(LL_DISPLAY_TOPIC)
    else:
        mqtt_ready = 0
        retry_time = 2
        while rc != 0:
            time.sleep(retry_time)
            try:
                rc = mqtt_client.reconnect()
            except Exception as e:
                rc = 1
                retry_time = 10  # probably wifi/internet problem so slow down the reconnect periode


if __name__ == "__main__":

    aas = AasI2C()

    mqttc = mqtt.Client()
    mqttc.connect("localhost")
    mqttc.publish(LL_I2C_MSG_TOPIC, "I2C: prepared")
    mqttc.on_connect = on_connect
    mqttc.user_data_set(aas)
    mqttc.message_callback_add(LL_DISPLAY_TOPIC, on_display)

    aas.display_begin()

    if not aas.display_ready:
        mqttc.publish(LL_I2C_MSG_TOPIC, "I2C: display is not ready")

    aas.load_fonts(10)
    aas.load_fonts(12)
    aas.load_fonts(15)

    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell=True)

    txt = u"IP: " + str(IP, "ascii") + ""

    aas.draw.text((2, 10), txt, font=aas.fonts["Arial-12"], fill=255)

    aas.display.image(aas.image)
    aas.send_to_display()

    while 1:
        mqttc.loop()

        if aas.display_command == "clear":
            aas.clear_display()
            aas.clear_display_buffer()
        elif aas.display_command == "write":
            aas.draw.text((aas.write_text["pos_x"], aas.write_text["pos_y"]), aas.write_text["text"], font=aas.fonts[aas.write_text["font"]], fill=255)
            aas.display.image(aas.image)
            aas.send_to_display()
            aas.clear_display_buffer()

        if not aas.display_ready:
            aas.display_begin()
