#!/bin/sh

sudo cp service/aas-low-level.service /lib/systemd/system/aas-low-level.service
sudo systemctl enable aas-low-level.service
sudo systemctl start aas-low-level.service
