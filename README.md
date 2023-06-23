# schanz-rolladen-raspi
Remote Control 433MHz Schanz Rolladen with Raspi

** Status: WIP **


# How to reverse engineer

+ Frequency Range of the remote control is at about 433.950 MHz (Found out pressing one button while tuning with my Yaesu FT 817)
+ Connect a RTL SDR to a raspi

## Prepare the raspi
+ Installation script: `./install.sh`

## Store the button signals
+ Start copying the button signals using `./rtlmenu.sh`: Record, set frequency (433.950 in my case), set gain to 0 (AGC), record.
+ Play back using `sudo ./sendiq -s 250000 -f 433.9500e6 -t u8 -i record.iq` (without wire antenna on GPIO7, so that the range is only in centimeters)
+ I checked the output using my Yaesu FT 817
+ One working save the record.iq file to buttonX.iq and continue with the next button.



# Installing the MQTT service
+ `pip3 install -r requirements.txt`

# Testing the installation
+ Install mosquitto, i.e. on osx: `brew install mosquitto`
```
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m <Up|Down|Stop|Percent>
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Up
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Down
mosquitto_pub -h t20 -t rollershutter/control/Test1 -m Stop
mosquitto_sub -h t20 -t rollershutter/Test1/percentage
```



# References
- https://hagensieker.com/2019/01/12/rpitx-replay-attack-on-ge-myselectsmart-remote-control-outlet/