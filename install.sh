#!/bin/bash
sudo apt-get update 
sudo apt-get -y upgrade
sudo apt-get -y install git python3-pip
git clone https://github.com/F5OEO/rpitx
cd rpitx
./install.sh

sudo chmod +s /usr/bin/sendiq

cd 
git clone https://github.com/8cH9azbsFifZ/schanz-rolladen-raspi.git
pip3 install -r requirements.txt

cd schanz-rolladen-raspi
sudo cp rollershutter.service /etc/systemd/system/test.service
sudo systemctl daemon-reload
sudo systemctl enable test.service
sudo systemctl start test.service


sudo reboot