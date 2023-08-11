# schanz-rolladen-raspi
Remote Control 433MHz Schanz Rolladen with Raspi

** Status: WIP **

# Installing the MQTT service
+ Prepare a raspi with a fresh raspian
+ `apt-get -y install python3-pip`
+ `git clone https://github.com/8cH9azbsFifZ/schanz-rolladen-raspi.git`
+ `cd schanz-rolladen-raspi/ && pip3 install -r requirements.txt`

## Installing the service
```
cd /opt
sudo git clone https://github.com/8cH9azbsFifZ/schanz-rolladen-raspi.git
cd schanz-rolladen-raspi
sudo pip3 install -r requirements.txt
sudo cp rollershutter.service /etc/systemd/system/rollershutter.service
sudo systemctl daemon-reload
sudo systemctl enable rollershutter.service
sudo systemctl start rollershutter.service

```

### Uninstalling the service
```
sudo systemctl stop rollershutter.service
sudo systemctl disable rollershutter.service
sudo rm  /etc/systemd/system/rollershutter.service
```

# Testing the installation
+ Install mosquitto, i.e. on osx: `brew install mosquitto`
```
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m <Open|Close|Stop|0-100>
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Open
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Close
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Stop
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m 30
mosquitto_sub -h t20 -t rollershutter/Test1/percentage
```


# References
- The motor is a Siral EL4F motor with 433 MHz remote control: https://www.siral.de/index.php?id=127
- Using a realais: https://blog.berrybase.de/blog/2020/08/12/relais-steuerung-mit-dem-raspberry-pi-so-funktionierts/
- MQTT interface: https://www.home-assistant.io/integrations/cover.mqtt/
