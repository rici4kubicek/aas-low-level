#!/bin/sh
mkdir ./log
chmod a+x low-level-spi.py
sudo apt-get -y --force-yes  update
sudo apt-get -y --force-yes install python-pip
pip install -r requirements.txt
sudo apt-get -y --force-yes install mosquitto
sudo apt-get -y --force-yes install mosquitto-clients
cd
git clone https://github.com/nightseas/python-nightWiring
cd python-nightWiring
git submodule init && git submodule update
sudo python setup.py install
