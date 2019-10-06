#!/bin/sh
mkdir ./log
chmod a+x low-level-spi.py
sudo apt-get update
sudo apt-get install python-pip
pip install -r requirements.txt
sudo apt-get install mosquitto
sudo apt-get install mosquitto-clients