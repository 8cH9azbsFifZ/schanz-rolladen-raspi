# Experimental with Raspi 

** Scrapbook **

- Experimental relais controls on pins 16 and 18
- Reverse engineering using fhem, minicul and signalduino


# Testing with minicul
- https://github.com/RFD-FHEM/SIGNALDuino/releases
sudo avrdude -c arduino -b57600 -P /dev/ttyUSB0 -p atmega328p -vv -U SIGNALDuino_miniculcc1101_3.5.0.hex
picocom /dev/ttyUSB0 -b 57600
- https://github.com/RFD-FHEM/SIGNALDuino/wiki/Commands


### With FHEM


cf. Tedsen_SKX2xx


deviceCode = 1FFF1F0
protocol 46


### Open
set sigduino sendMsg P46#111010101110001010#R10
docker-compose exec fhem perl /opt/fhem/fhem.pl 7072 "set sigduino sendMsg P46#111010101110001010#R10"
data open EAE28

fhem_1  | 2023.08.11 14:38:17.444 1: sigduino: SD_UT_Parse UNDEFINED sensor unknown detected, protocol 46, data EAE28, code 1FFF1F0
000101010001110101

fhem_1  | 2023.08.11 15:39:35.749 1: sigduino: SD_UT_Parse UNDEFINED sensor unknown detected, protocol 46, data EAE28, code 1FFF1F0 and GEROLF 1FFF1F0FF

FF => 1010 

### Close
set sigduino sendMsg P46#111010101110001000#R10
docker-compose exec fhem perl /opt/fhem/fhem.pl 7072 "set sigduino sendMsg P46#111010101110001000#R10"
data close EAE20

fhem_1  | 2023.08.11 14:38:10.427 1: sigduino: SD_UT_Parse UNDEFINED sensor unknown detected, protocol 46, data EAE20, code 1FFF1F0
000101010001110111
fhem_1  | 2023.08.11 15:40:00.439 1: sigduino: SD_UT_Parse UNDEFINED sensor unknown detected, protocol 46, data EAE20, code 1FFF1F0 and GEROLF 1FFF1F0F0
=> TRISTATE CODE
F0 =>  1000


fhem_1  | 2023.08.11 16:09:48.838 4: sigduino: SD_UT protocol 46, bitData 11101010111000101000, hlen 5

### Refs

https://hub.docker.com/r/fhem/fhem

https://github.com/fhem/fhem-docker/blob/dev/docker-compose.yml
https://www.fhemwiki.de/wiki/SIGNALduino
https://www.fhemwiki.de/wiki/Unbekannte_Funkprotokolle#Ansatz_1_-_Versuchen
https://github.com/RFD-FHEM/SIGNALDuino/issues/293
/dev/ttyUSB0@57600

/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0


