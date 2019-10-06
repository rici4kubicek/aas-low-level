#!/bin/sh
mkdir ./log
chmod a+x low-level-spi.py
sudo apt-get -y --force-yes  update
sudo apt-get -y --force-yes install python-pip
pip install -r requirements.txt
sudo apt-get -y --force-yes install mosquitto
sudo apt-get -y --force-yes install mosquitto-clients