#!/bin/bash
APP_PATH="/home/sqylab/Projet-RFID/"
cd ${APP_PATH}
redis-server & echo $! > pid 
sudo python3 ${APP_PATH}Badge.py & echo $! >> pid 
echo $PWD
# source ./venv/bin/activate
sudo python3 Web_app.py & echo $! >> pid
sudo python3 modules/telegram.py & echo $! >> pid
exit 0
