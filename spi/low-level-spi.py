#!/usr/bin/env python2
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
from tools.nanopi_spi import *
from tools.mfrc522 import *
from tools.shutdown import *
from tools.apa102 import *
import paho.mqtt.client as mqtt
import json
import os
import time

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"

LL_SPI_TOPIC = "spi"
LL_READER_TOPIC = LL_SPI_TOPIC + "/reader"
LL_READER_DATA_TOPIC = LL_READER_TOPIC + "/data"
LL_READER_DATA_READ_TOPIC = LL_READER_TOPIC + "/data/read"
LL_READER_DATA_WRITE_TOPIC = LL_READER_TOPIC + "/data/write"
LL_SPI_MSG_TOPIC = LL_SPI_TOPIC + "/msg"
LL_LED_TOPIC = LL_SPI_TOPIC + "/led"


class AasSpi(object):
    def __init__(self):
        self.nanopi = None
        self.led = None
        self.logger = None
        self.send_led = False
        self.write_data = {}
        self.write_data_flag = False


def on_leds(moqs, obj, msg):
    obj.logger.debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload))

    try:
        data = json.loads(msg.payload)
        obj.led.prepare_data(data["led_0"]["red"], data["led_0"]["green"], data["led_0"]["blue"],
                             data["led_0"]["brightness"], 0)
        obj.led.prepare_data(data["led_1"]["red"], data["led_1"]["green"], data["led_1"]["blue"],
                             data["led_1"]["brightness"], 1)
        obj.led.prepare_data(data["led_2"]["red"], data["led_2"]["green"], data["led_2"]["blue"],
                             data["led_2"]["brightness"], 2)
        obj.led.prepare_data(data["led_3"]["red"], data["led_3"]["green"], data["led_3"]["blue"],
                             data["led_3"]["brightness"], 3)
        obj.send_led = True
    except:
        obj.logger.error("MQTT: received msq is not json with expected information")


def on_write(moqs, obj, msg):
    obj.logger.debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload))

    try:
        data = json.loads(msg.payload)
        obj.write_data["sector"] = data["sector"]
        obj.write_data["data"] = data["data"]
        obj.logger.debug(obj.write_data)
        obj.write_data_flag = True
    except:
        obj.logger.error("MQTT: received msq is not json with expected information")


def on_connect(mqtt_client, obj, flags, rc):
    global mqtt_ready
    if rc==0:
        obj.logger.info("MQTT: Connected ")
        mqtt_ready = 1
        mqttc.subscribe(LL_LED_TOPIC)
        mqttc.subscribe(LL_READER_DATA_WRITE_TOPIC)
    else:
        mqtt_ready = 0
        retry_time = 2
        while rc != 0:
            time.sleep(retry_time)
            obj.logger.info("MQTT: Reconnecting ...")
            try:
                rc = mqtt_client.reconnect()
            except Exception as e:
                obj.logger.error("MQTT: Connection request error (Code: {c}, Message: {m})!"
                    .format(c=type(e).__name__, m=str(e)))
                rc = 1
                retry_time = 10  # probably wifi/internet problem so slow down the reconnect periode


if __name__ == "__main__":

    aas = AasSpi()

    logging.basicConfig(level=logging.DEBUG)
    aas.logger = logging.getLogger(__name__)
    try:
        handler = logging.handlers.RotatingFileHandler("home/pi/aas-low-level/log/low-level-spi.txt", maxBytes=100000, backupCount=10)
    except:
        handler = logging.handlers.RotatingFileHandler("log/low-level-spi.txt", maxBytes=100000,
                                                       backupCount=10)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    aas.logger.addHandler(handler)

    aas.logger.info("Core: ===================== Application start ========================")
    aas.logger.info("Script version: {}".format(__version__))

    shutdown = EShutdown()

    aas.nanopi = NanoPiSpi()
    aas.nanopi.led_cs_init()
    aas.nanopi.led_cs_set(1)
    aas.nanopi.open(0, 0, 100000)

    aas.led = APA102(4)

    aas.led.prepare_data(0, 0, 0, 0, 0)
    aas.led.prepare_data(0, 0, 0, 0, 1)
    aas.led.prepare_data(0, 0, 0, 0, 2)
    aas.led.prepare_data(0, 0, 0, 0, 3)

    aas.nanopi.led_cs_init()
    aas.nanopi.led_cs_set(1)
    aas.nanopi.write(aas.led.get_data())
    aas.nanopi.led_cs_set(0)

    aas.nanopi.reader_reset_init()
    aas.nanopi.reader_reset_set(1)

    MIFAREReader = MFRC522(aas.nanopi)

    mqttc = mqtt.Client()
    mqttc.connect("localhost")
    mqttc.publish(LL_SPI_MSG_TOPIC, "SPI is prepared")
    mqttc.on_connect = on_connect
    mqttc.user_data_set(aas)
    mqttc.message_callback_add(LL_LED_TOPIC, on_leds)
    mqttc.message_callback_add(LL_READER_DATA_WRITE_TOPIC, on_write)

    while True:

        mqttc.loop()

        card_data = {}
        # Scan for cards
        (status, TagType) = MIFAREReader.request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            mqttc.publish(LL_READER_TOPIC, "Some card detected")
            aas.logger.debug("CARD: card detected")
            card_data["timestamp"] = time.time()

        # Get the UID of the card
        (status, uid) = MIFAREReader.anticoll(1)

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            aas.logger.debug("Card read UID: {}, {}, {}, {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]), hex(uid[3])))
            # place read uid to dict
            card_data["uid"] = uid
            MIFAREReader.select_tag(uid)
            card_data["data"] = MIFAREReader.dump_ultralight(uid)

            if aas.write_data_flag:
                aas.logger.debug(
                    "Card UID: {}, {}, {}, {} write data to sector".format(hex(uid[0]), hex(uid[1]), hex(uid[2]),
                                                                           hex(uid[3]), aas.write_data["sector"]))
                MIFAREReader.write(aas.write_data["sector"], aas.write_data["data"])
                aas.write_data_flag = False

            MIFAREReader.stop_crypto1()

            mqttc.publish(LL_READER_DATA_READ_TOPIC, json.dumps(card_data))

        if aas.send_led:
            aas.nanopi.led_cs_set(1)
            aas.nanopi.write(aas.led.get_data())
            aas.nanopi.led_cs_set(0)
            aas.send_led = False

        if shutdown.killed:
            break

    mqttc.publish(LL_SPI_MSG_TOPIC, "SPI LL shutdown")