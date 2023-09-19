import logging
import fhem


#class Rollershutter():
#    def __init__(self, TimeOpen = 53. , TimeClose = 53., MQTThostname = "t20", mqtt_port=1883, FHEMhostname = "minicul-raspi", fhem_port=8083, RollershutterName="Test1", Simulation = False):
#        self._fhem = fhem.Fhem(FHEMhostname, protocol="http", port=fhem_port)

#            self._fhem.send_cmd("define sigduino SIGNALduino /dev/ttyUSB0@57600") # FIXME: make configurable

FHEMhostname = "minicul-raspi"
fhem_port=8083

_fhem = fhem.Fhem(FHEMhostname, protocol="http", port=fhem_port)
_fhem.send_cmd("help") 
ttt = _fhem.get_device_reading("sigduino")
print (ttt)
print (len(ttt))

ttt = _fhem.get_device_reading("sigduino1")
print (ttt)

print (len(ttt))