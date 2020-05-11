# aas-low-level

## Installation
**Note** This is applicable only if you place `aas-low-level` project to path `/home/pi/aas-low-level/`

* run command `sh install.sh` in directory `/home/pi/aas-low-level/`
* run command `sh start_service.sh` in directory `/home/pi/aas-low-level/`

**Note** If you have project `aas-low-level` placed on another path, you must make some changes in `aas-low-level.service` file
* change _WorkingDirectory_ to path, where is your project placed
* change _ExecStartPre_ if you want another conditions, or your device is not in network, which is routed to the internet
* change _ExecStart_ to path, where is your project main file, `aas-low-level.py`
* run command `sh install.sh` in directory `/home/pi/aas-low-level/`
* run command `sh start_service.sh` in directory `/home/pi/aas-low-level/`