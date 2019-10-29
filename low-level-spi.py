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
LL_SPI_MSG_TOPIC = LL_SPI_TOPIC + "/msg"
LL_LED_TOPIC = LL_SPI_TOPIC + "/led"


def on_leds(moqs, obj, msg):
    print(msg.payload)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    try:
        handler = logging.handlers.RotatingFileHandler("home/pi/aas-low-level/log/low-level-spi.txt", maxBytes=100000, backupCount=10)
    except:
        handler = logging.handlers.RotatingFileHandler("log/low-level-spi.txt", maxBytes=100000,
                                                       backupCount=10)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.info("Core: ===================== Application start ========================")
    logger.info("Script version: {}".format(__version__))

    shutdown = EShutdown()

    nano_pi = NanoPiSpi()
    nano_pi.open(0, 0, 100000)

    nano_pi.reader_reset_init()
    nano_pi.reader_reset_set(1)
    time.sleep(0.5)
    nano_pi.reader_reset_set(0)
    time.sleep(0.5)
    nano_pi.reader_reset_set(1)

    led = APA102(4)

    led.prepare_data(r=100, g=0, b=0, brightness=10, led_idx=0)
    led.prepare_data(r=0, g=100, b=0, brightness=25, led_idx=1)
    led.prepare_data(r=0, g=0, b=100, brightness=60, led_idx=2)
    led.prepare_data(r=100, g=100, b=100, brightness=20, led_idx=3)

    nano_pi.led_cs_init()
    nano_pi.led_cs_set(1)
    nano_pi.write(led.get_data())
    nano_pi.led_cs_set(0)

    MIFAREReader = MFRC522(nano_pi)

    mqttc = mqtt.Client()
    mqttc.connect("localhost")
    mqttc.publish(LL_SPI_MSG_TOPIC, "SPI is prepared")
    mqttc.message_callback_add(LL_LED_TOPIC, on_leds)

    while True:
        card_data = {}
        # Scan for cards
        (status, TagType) = MIFAREReader.request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            mqttc.publish(LL_READER_TOPIC, "Some card detected")
            logger.debug("CARD: card detected")
            card_data["timestamp"] = time.time()

        # Get the UID of the card
        (status, uid) = MIFAREReader.anticoll(1)

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            logger.debug("Card read UID: {}, {}, {}, {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]), hex(uid[3])))
            # place read uid to dict
            card_data["uid"] = uid
            MIFAREReader.select_tag(uid)
            card_data["data"] = MIFAREReader.dump_ultralight(uid)
            MIFAREReader.stop_crypto1()

            mqttc.publish(LL_READER_DATA_READ_TOPIC, json.dumps(card_data))

        if shutdown.killed:
            break

    mqttc.publish(LL_SPI_MSG_TOPIC, "SPI LL shutdown")