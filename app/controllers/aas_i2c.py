import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageChops
from app.touch_control import TouchControl
from app.scroll_text import ScrollText
from app import *
import os
import fnmatch
import json
import subprocess


class AasI2C:
    def __init__(self):
        self.display = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus='0')
        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.fonts = {}
        self.write_text = {}
        self.display_command = None
        self.display_ready = False
        self.touch = TouchControl(i2c_bus="0")
        self.scroll = ScrollText(self)
        self._send = False
        self.scroll.set_send = self.set_send

    def set_send(self):
        self._send = True

    def on_event(self, topic, message):
        pass

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
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
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
        self.on_event(LL_TOUCH_TOPIC, json.dumps(msg))

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
        self.scroll.prepare()
        self._send = False

    def display_loop(self):
        if self.display_command == "clear":
            self.clear_display()
            self.clear_display_buffer()
            self.scroll.allow = False
        elif self.display_command == "write":
            self.draw.text((self.write_text["pos_x"], self.write_text["pos_y"]), self.write_text["text"],
                           font=self.fonts[self.write_text["font"]], fill=255)
            self.clear_display_buffer()
            self._send = True
        elif self.display_command == "scroll":
            self.scroll.text = self.write_text["text"]
            self.scroll.font = self.write_text["font"]
            self.scroll.y_pos = self.write_text["pos_y"]
            self.scroll.allow = True
            self.clear_display_buffer()

        if self._send:
            self.display.image(self.image)
            self.send_to_display()
            self._send = False

        self.scroll.run()

        if not self.display_ready:
            self.display_begin()