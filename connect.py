import logging
import fhem

logging.basicConfig(level=logging.DEBUG)


open_command = "set sigduino sendMsg P46#111010101110001010#R10"
close_command = "set sigduino sendMsg P46#111010101110001000#R10"

fh = fhem.Fhem("raspimatic-raspi-wlan", protocol="http", port=8083)
# Send a command to FHEM (this automatically connects() in case of telnet)
fh.send_cmd(open_command)
