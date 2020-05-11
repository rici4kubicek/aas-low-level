import os
import fnmatch
import json
import subprocess
import time
from app import *
from app.nanopi_spi import NanoPiSpi
from app.apa102 import APA102
from app.mfrc522 import MFRC522
from app.tag_helper import *


class AasSpi:
    def __init__(self):
        self.nano_pi = NanoPiSpi()
        self.led = APA102(4)
        self.send_led = False
        self.write_data = {}
        self.write_data_flag = False
        self.write_multi_data_flag = False
        self.old_read_data = []
        self.count_of_pages_to_write = 0

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

    def on_event(self, topic, message):
        pass

    def log_debug(self, message):
        pass

    def publish_write_status(self, status, sector):
        data = {"write": {"sector": 0, "status": "NONE"}}
        data["write"]["sector"] = sector
        data["write"]["status"] = status
        self.on_event(LL_READER_STATUS_TOPIC, json.dumps(data))

    def write_multi_to_tag(self, uid):
        uid[0] = uid[1]
        uid[1] = uid[2]
        uid[2] = uid[3]

        self.mifare_reader.sak(uid)

        (status, uid2) = self.mifare_reader.anticoll(2)
        uid[3] = uid2[0]
        uid[4] = uid2[1]
        uid.append(uid2[2])
        uid.append(uid2[3])
        self.mifare_reader.select_tag2(uid)
        self.log_debug(
            "Card UID: {}, {}, {}, {} write multi data to sectors {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]),
                                                                             hex(uid[3]),
                                                                             self.write_data["write_multi"]))
        i = 0
        while i < self.count_of_pages_to_write:
            status = self.mifare_reader.write(self.write_data["write_multi"][i]["sector"],
                                              self.write_data["write_multi"][i]["data"])
            if status == self.mifare_reader.MI_OK:
                self.publish_write_status("OK", self.write_data["write_multi"][i]["sector"])
                i = i + 1
            else:
                self.publish_write_status("NOK", self.write_data["write_multi"][i]["sector"])

        if i == self.count_of_pages_to_write:
            self.write_multi_data_flag = False

    def write_to_tag(self, uid):
        uid[0] = uid[1]
        uid[1] = uid[2]
        uid[2] = uid[3]

        self.mifare_reader.sak(uid)

        (status, uid2) = self.mifare_reader.anticoll(2)
        uid[3] = uid2[0]
        uid[4] = uid2[1]
        uid.append(uid2[2])
        uid.append(uid2[3])
        self.mifare_reader.select_tag2(uid)
        self.log_debug(
            "Card UID: {}, {}, {}, {} write data to sector".format(hex(uid[0]), hex(uid[1]), hex(uid[2]),
                                                                   hex(uid[3]), self.write_data["sector"]))
        status = self.mifare_reader.write(self.write_data["sector"], self.write_data["data"])
        if status == self.mifare_reader.MI_OK:
            self.publish_write_status("OK", self.write_data["sector"])
            self.write_data_flag = False
        else:
            self.publish_write_status("NOK", self.write_data["sector"])

    def reader_loop(self):
        card_data = {}
        # Scan for cards
        (status, TagType) = self.mifare_reader.request(self.mifare_reader.PICC_REQIDL)

        # If a card is found
        if status == self.mifare_reader.MI_OK:
            self.on_event(LL_READER_TOPIC, "Some card detected")
            self.log_debug("CARD: card detected")
            card_data["timestamp"] = time.time()

        # Get the UID of the card
        (status, uid) = self.mifare_reader.anticoll(1)

        # If we have the UID, continue
        if status == self.mifare_reader.MI_OK:
            if not self.write_data_flag and not self.write_multi_data_flag:
                self.log_debug(
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
                    self.on_event(LL_READER_DATA_READ_TOPIC, json.dumps(card_data))
                self.old_read_data = card_data["data"]
            elif self.write_data_flag:
                self.write_to_tag(uid)
            elif self.write_multi_data_flag:
                self.log_debug("Write multi data")
                self.write_multi_to_tag(uid)

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
