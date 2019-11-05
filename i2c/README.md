# aas-low-level i2c

## Script installation
* copy file `low-level-i2c.service` from directory `service` to directory  `/lib/systemd/system`
* run `systemctl enable low-level-i2c.service`
* go through the guide with your username and password
* start of service `systemctl start low-level-i2c.service`
* status of service `systemctl status low-level-i2c.service`

### MQTT structure
* there are a few of MQTT topics on localhost broker:
    * `i2c/msg` - general, text oriented information from i2c low-level layer
    * `i2c/display` - commands for display in json format
#### Structure of _json_ message in `i2c/display` topic
* string `cmd` with text `clear` or `write`
* if `cmd` _write_ is placed, script expect other parts of _json_:
    * string `text` required text
    * string `font` required font; available fonts:
        * `Arial-10` - _Arial_ with size 10px
        * `Arial-12` - _Arial_ with size 12px
        * `Arial-15` - _Arial_ with size 15px
        * `Vafle_VUT_Regular-10` - _Vafle VUT Regular_ with size 10px
        * `Vafle_VUT_Regular-12` - _Vafle VUT Regular_ with size 12px
        * `Vafle_VUT_Regular-15` - _Vafle VUT Regular_ with size 15px
    * number `pos_x` with target position of text start on x axis
    * number `pos_y` with target position of text start on y axis
* if `cmd` _clear_ is placed, display is cleared
        