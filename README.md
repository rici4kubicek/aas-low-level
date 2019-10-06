# aas-low-level

## Stage 1
**Read UID and data from tag and send it throw mqtt to local broker**
### Note
**It is necessary to place whole repository to directory /home/pi/aas-low-level**
### Preparation
* run bash script _install.sh_
    * this script install necessary parts include mqtt broker, mqtt clients, pip, python libraries
    * run `sh ./install.sh`
### Run
* run bash script _run.sh_
    * run `sh ./run.sh`

### MQTT structure
* there are a few of MQTT topics on localhost broker:
    * `spi/msg` - general, text oriented information from spi low-level layer
    * `spi/reader` - general, text oriented information from reader
    * `spi/reader/data/read` - data read from tag in json format
#### Structure of _json_ message in `spi/reader/data/read` topic
* array `data` with 16 sub-arrays with 16 bytes
* array `uid` with 5 bytes
* number `timestamp` with timestamp of rfid tag attached event