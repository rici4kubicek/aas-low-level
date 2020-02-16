#!/bin/sh
mkdir ./log
chmod a+x low-level-spi.py
sudo apt-get -y --force-yes  update
sudo apt-get -y --force-yes install python3-pip
sudo pip3 install -r requirements.txt
sudo apt-get -y --force-yes install mosquitto
sudo apt-get -y --force-yes install mosquitto-clients
cd
git clone https://github.com/nightseas/python-nightWiring
cd python-nightWiring
git submodule init && git submodule update
sudo python3 setup.py install
cd
sudo rm -r python-nightWiring
cd aas-low-level/spi
