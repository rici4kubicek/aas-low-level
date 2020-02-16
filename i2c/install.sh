#!/bin/sh
sudo apt-get -y --force-yes  update
sudo apt-get -y --force-yes install libtiff5-dev libjpeg8-dev libopenjp2-7-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk libharfbuzz-dev libfribidi-dev
cd
git clone https://github.com/python-pillow/Pillow.git
cd
cd Pillow
sudo python3 setup.py install
cd
sudo rm -r Pillow
cd aas-low-level/i2c
sudo pip3 install -r requirements.txt
