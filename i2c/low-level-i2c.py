#!/usr/bin/env python2
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

LL_I2C_TOPIC = "i2c"
LL_DISPLAY_TOPIC = LL_I2C_TOPIC + "/display"
LL_I2C_MSG_TOPIC = LL_I2C_TOPIC + "/msg"

def on_connect(mqtt_client, obj, flags, rc):
    global mqtt_ready
    if rc==0:
        obj.logger.info("MQTT: Connected ")
        mqtt_ready = 1
        mqttc.subscribe(LL_DISPLAY_TOPIC)
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

    mqttc = mqtt.Client()
    mqttc.connect("localhost")
    mqttc.publish(LL_I2C_MSG_TOPIC, "I2C is prepared")
    mqttc.on_connect = on_connect
    # mqttc.user_data_set(aas)
    # mqttc.message_callback_add(LL_DISPLAY_TOPIC, on_display)