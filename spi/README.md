# aas-low-level - SPI part

## Stage 1
**Read UID and data from tag and send it throw mqtt to local broker**
### Note
**It is necessary to place whole repository to directory /home/pi/aas-low-level/spi**
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

## Stage 2
**Write color data received from MQTT to LEDs**

### MQTT structure
* new data topic:
    * `spi/led` - led control topic in json format
#### Structure of _json_ message in `spi/led` topic
* four objects with four entries
* objects are named like `led_0`, `led_1`, `led_2`, `led_3`
* each object has entry `red`, `green`, `blue` for color components and `brightness` for brightness value
* color components range is 0 - 255, brightness range is 0-100 (in percents)

## Stage 3
**Write data received from MQTT to tag memory on defined position**

### MQTT structure
* new data topic:
    * `spi/reader/data/write` - data write topic in json format
#### Structure of _json_ message in `spi/reader/data/write` topic
* page address in field `sector`
* four bytes in array `data`
