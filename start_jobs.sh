#!/bin/bash
APP_PATH="/home/michel/Projet-RFID/"
cd ${APP_PATH}
redis-server & echo $! > pid 
sudo python3 ${APP_PATH}Badge.py & echo $! >> pid 
echo $PWD
source ./venv/bin/activate
python Web_app.py & echo $! >> pid
python modules/telegram.py & echo $! >> pid
exit 0
