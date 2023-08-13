# schanz-rolladen-raspi
Remote Control 433MHz Schanz Rolladen with Raspi

Using a minicul and the SIGNALduino FHEM module create an interface for a rollershutter using MQTT. 
FHEM is encapsulated in a separate container only for the purpose of sending the 433,95 MHz commands
to the rollershutter motor. A separate container provides a python script for sending the commands to fhem
and serving an interface using MQTT.

Thus this module is compatible with HomeAssistang and OpenHab.

![minicul](experiments/doc/minicul.png)

# Installation

## Configuring the varibles for the containers
Configure the following variables in the `docker-compose.yml`` file: 
`MQTT_HOST MQTT_PORT FHEM_HOST FHEM_PORT TIME_OPEN TIME_CLOSE ROLLERSHUTTER_NAME``
If variable `SIMULATION` is defined, run in simulation mode.

### Testing the installation
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

## Configuration for HomeAssistang
+ Install the MQTT integration and provide your server
+ Copy and adjust the configuration in `homeassistant-config.yaml` to your setup

## Configuration for OpenHAB
+ Install the mqtt binding
+ Copy and adjust the things configuration ![Things](openhab.things)
+ Copy and adjust the item configuration ![Item](openhab.items)


# References
- The motor is a Siral EL4F motor with 433 MHz remote control: https://www.siral.de/index.php?id=127
- MQTT interface: https://www.home-assistant.io/integrations/cover.mqtt/
- Using SIGNALduino https://wiki.fhem.de/wiki/SIGNALduino
- And FHEM https://wiki.fhem.de/wiki/Hauptseite
- OpenHAB MQTT integration https://www.openhab.org/addons/bindings/mqtt.generic/
