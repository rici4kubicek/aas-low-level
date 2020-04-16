#!/usr/bin/env python3
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
LL_READER_STATUS_TOPIC = LL_READER_TOPIC + "/state"
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
        self.write_multi_data_flag = False
        self.mqtt = None


def on_leds(moqs, obj, msg):
    obj.logger.debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))
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
    obj.logger.debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        if "write" in data:
            obj.write_data["sector"] = data["write"][0]["sector"]
            obj.write_data["data"] = data["write"][0]["data"]
            obj.logger.debug(obj.write_data)
            obj.write_data_flag = True
            obj.write_multi_data_flag = False
            obj.count_of_pages_to_write = len(data["write"])
        elif "write_multi" in data:
            print(data["write_multi"])
            obj.write_data["write_multi"] = data["write_multi"]
            obj.logger.debug(obj.write_data)
            obj.write_data_flag = False
            obj.write_multi_data_flag = True
            obj.count_of_pages_to_write = len(data["write_multi"])
    except:
        obj.logger.error("MQTT: received msq is not json with expected information")


def on_connect(mqtt_client, obj, flags, rc):
    global mqtt_ready
    if rc == 0:
        obj.logger.info("MQTT: Connected ")
        mqtt_ready = 1
        obj.mqtt.subscribe(LL_LED_TOPIC)
        obj.mqtt.subscribe(LL_READER_DATA_WRITE_TOPIC)
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


def publish_write_status(aas, status, sector, mqtt):
    data = {"write": {"sector": 0, "status": "NONE"}}
    data["write"]["sector"] = sector
    data["write"]["status"] = status
    mqtt.publish(LL_READER_STATUS_TOPIC, json.dumps(data))


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
        publish_write_status(aas, "OK", aas.write_data["sector"], mqttc)
        aas.write_data_flag = False
    else:
        publish_write_status(aas, "NOK", aas.write_data["sector"], mqttc)


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
            publish_write_status(aas, "OK", aas.write_data["write_multi"][i]["sector"], mqttc)
            i = i + 1
        else:
            publish_write_status(aas, "NOK", aas.write_data["write_multi"][i]["sector"], mqttc)

    if i == aas.count_of_pages_to_write:
        aas.write_multi_data_flag = False


def main():
    aas = AasSpi()
    aas.logger = logging.getLogger()
    aas.logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/var/log/low-level-spi.txt")
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

    shutdown = EShutdown()

    aas.nanopi = NanoPiSpi()
    aas.nanopi.led_cs_init()
    aas.nanopi.led_cs_set(1)
    aas.nanopi.open(0, 0, 2000000)

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

    aas.mqtt = mqtt.Client()
    aas.mqtt.connect("localhost")
    aas.mqtt.publish(LL_SPI_MSG_TOPIC, "SPI is prepared")
    aas.mqtt.on_connect = on_connect
    aas.mqtt.user_data_set(aas)
    aas.mqtt.message_callback_add(LL_LED_TOPIC, on_leds)
    aas.mqtt.message_callback_add(LL_READER_DATA_WRITE_TOPIC, on_write)

    old_read_data = []

    while True:

        aas.mqtt.loop()

        card_data = {}
        # Scan for cards
        (status, TagType) = MIFAREReader.request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            aas.mqtt.publish(LL_READER_TOPIC, "Some card detected")
            aas.logger.debug("CARD: card detected")
            card_data["timestamp"] = time.time()

        # Get the UID of the card
        (status, uid) = MIFAREReader.anticoll(1)

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            if not aas.write_data_flag and not aas.write_multi_data_flag:
                aas.logger.debug("Card read UID: {}, {}, {}, {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]), hex(uid[3])))
                MIFAREReader.select_tag(uid)
                card_data["data"], state = MIFAREReader.dump_ultralight(uid)
                # properly parse UID from readed data
                card_data["uid"] = MIFAREReader.parse_serial_number(card_data["data"])
                if state == MIFAREReader.MI_OK:
                    card_data["read_state"] = "OK"
                else:
                    card_data["read_state"] = "ERROR"
                data = MIFAREReader.get_version()
                card_data["tag"] = tag_parse_version(data)
                if old_read_data != card_data["data"]:
                    aas.mqtt.publish(LL_READER_DATA_READ_TOPIC, json.dumps(card_data))
                old_read_data = card_data["data"]
            elif aas.write_data_flag:
                write_to_tag(uid, MIFAREReader, aas)
            elif aas.write_multi_data_flag:
                aas.logger.debug("Write multi data")
                write_multi_to_tag(uid, MIFAREReader, aas)

            MIFAREReader.stop_crypto1()
            (status, TagType) = MIFAREReader.request(MIFAREReader.PICC_HALT)
        else:
            old_read_data = []

        if aas.send_led:
            aas.nanopi.led_cs_set(1)
            aas.nanopi.write(aas.led.get_data())
            aas.nanopi.led_cs_set(0)
            aas.send_led = False

        if shutdown.killed:
            break

    aas.mqtt.publish(LL_SPI_MSG_TOPIC, "SPI LL shutdown")


if __name__ == "__main__":
    main()
