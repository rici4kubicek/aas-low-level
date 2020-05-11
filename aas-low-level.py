#!/usr/bin/python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt_client
import logging
import logging.handlers
from app.controllers.aas_i2c import *
from app.controllers.aas_spi import *

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "2.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"


class Aas:
    def __init__(self):
        self.i2c = AasI2C()
        self.spi = AasSpi()
        self.i2c.on_event = self.handle_event
        self.spi.on_event = self.handle_event
        self.spi.log_debug = self.logger_debug
        self.logger = logging.getLogger()
        self.mqtt = mqtt_client.Client()
        self.mqtt_ready = False

    def logger_debug(self, _str):
        self.logger.debug(_str)

    def logger_error(self, _str):
        self.logger.error(_str)

    def handle_event(self, topic, message):
        self.mqtt.publish(topic, message)


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
            obj.logger_debug(obj.spi.write_data)
            obj.spi.write_data_flag = True
            obj.spi.write_multi_data_flag = False
            obj.spi.count_of_pages_to_write = len(data["write"])
        elif "write_multi" in data:
            print(data["write_multi"])
            obj.spi.write_data["write_multi"] = data["write_multi"]
            obj.logger_debug(obj.spi.write_data)
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
            elif data["cmd"] == "scroll":
                obj.i2c.display_command = "scroll"
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
        obj.mqtt.subscribe(LL_DISPLAY_TOPIC)
        obj.mqtt.subscribe(LL_LED_TOPIC)
        obj.mqtt.subscribe(LL_READER_DATA_WRITE_TOPIC)
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
    aas = Aas()
    aas.logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/var/log/aas-low-level.txt")
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

    aas.mqtt.connect("localhost")
    aas.mqtt.on_connect = on_connect
    aas.mqtt.user_data_set(aas)
    aas.mqtt.message_callback_add(LL_DISPLAY_TOPIC, on_display)
    aas.mqtt.message_callback_add(LL_LED_TOPIC, on_leds)
    aas.mqtt.message_callback_add(LL_READER_DATA_WRITE_TOPIC, on_write)

    aas.i2c.display_begin()

    if not aas.i2c.display_ready:
        aas.mqtt.publish(LL_I2C_MSG_TOPIC, "I2C: display is not ready")

    aas.i2c.load_fonts(10)
    aas.i2c.load_fonts(12)
    aas.i2c.load_fonts(15)

    aas.i2c.init_screen()

    aas.mqtt.loop_start()

    while True:
        key = aas.i2c.touch.read_active_key()
        if key:
            aas.i2c.button_pressed_notification(key)

        aas.i2c.display_loop()

        aas.spi.reader_loop()

        aas.spi.led_loop()

        aas.i2c.touch.wait_events(0.1)


def touch_handle():
    touch = TouchControl(i2c_bus="0")

    while 1:
        key = touch.read_active_key()
        if key:
            print(key)
        touch.wait_events()


if __name__ == "__main__":
    main()
