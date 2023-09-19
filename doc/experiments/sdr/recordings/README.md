# Experimental SDR with Raspi 
- Experimental SDR on PIN7 using 433.9 MHz transmission (dead code as of 0.0.4)

** Scrapbook **



# How to reverse engineer the signals using SDR approach

+ Frequency Range of the remote control is at about 433.950 MHz (Found out pressing one button while tuning with my Yaesu FT 817)
+ Connect a RTL SDR to a raspi
![Raspi with RTL SDR](../img//raspi_rtl.png)

## Prepare the raspi
+ Installation script: 

```

git clone https://github.com/F5OEO/rpitx
cd rpitx
./install.sh

sudo chmod +s /usr/bin/sendiq

```

## Store the button signals
+ Start copying the button signals using `./rtlmenu.sh`: Record, set frequency (433.950 in my case), set gain to 0 (AGC), record.
+ Play back using `sudo ./sendiq -s 250000 -f 433.9500e6 -t u8 -i record.iq` (without wire antenna on GPIO7, so that the range is only in centimeters)
+ I checked the output using my Yaesu FT 817
+ One working save the record.iq file to buttonX.iq and continue with the next button.
+ You may shorten the signals afterwars using simply `dd if=button_close.iq of=button_close_short.iq bs=8 count=20000`

## Analyze using rtl_433
+ Install the tool: `brew install rtl_433`

### Close Button
+ `rtl_433 -A -r 250k:433.95M:cu8:button_close.iq`

Yields: Use a flex decoder with -X 'n=name,m=OOK_PWM,s=348,l=2076,r=15740,g=1984,t=691,y=0'

  [04] {18} 15 1d c0  : 00010101 00011101 11

![Close Button Pulse](../img/pulse_close.png)

### Open Button
+ `rtl_433 -A -r 250k:433.95M:cu8:button_open.iq`

Yields: Use a flex decoder with -X 'n=name,m=OOK_PWM,s=332,l=2064,r=15748,g=2004,t=693,y=0'

  [04] {18} 15 1d 40  : 00010101 00011101 01

![Open Button Pulse](../img/pulse_open.png)





# References
- https://hagensieker.com/2019/01/12/rpitx-replay-attack-on-ge-myselectsmart-remote-control-outlet/
- RTL SDR IQ Format: *.cu8 - Complex 8-bit unsigned integer samples (RTL-SDR) https://k3xec.com/packrat-processing-iq/
- Formats https://github.com/glv2/convert-samples
- RTL 433 Tool https://github.com/merbanan/rtl_433