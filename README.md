# schanz-rolladen-raspi
Remote Control 433MHz Schanz Rolladen with Raspi

Using a minicul and the SIGNALduino FHEM module create an interface for a rollershutter using MQTT. 
The MQTT topics are compatible with HomeAssistant.

![minicul](experiments/doc/minicul.png)


# Testing the installation
+ Install mosquitto, i.e. on osx: `brew install mosquitto`
+ Set position topic:  0-100 `mosquitto_pub -h t20 -t rollershutter/control_position/Test1 -m 30`
+ Set control topic: Open, Close, Stop
```
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Open
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Close
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Stop
```
+ State topic: open, closed, opening, closing, stopped - `mosquitto_sub -h t20 -t rollershutter/Test1/state`
+ Position topic: 0-100 - `mosquitto_sub -h t20 -t rollershutter/Test1/percentage`


# References
- The motor is a Siral EL4F motor with 433 MHz remote control: https://www.siral.de/index.php?id=127
- MQTT interface: https://www.home-assistant.io/integrations/cover.mqtt/
- Using SIGNALduino https://wiki.fhem.de/wiki/SIGNALduino
- And FHEM https://wiki.fhem.de/wiki/Hauptseite