cd /home/michel/Projet-RFID/
source venv/bin/activate
redis-server & echo $! > pid
sudo python3 Badge.py & echo $! >> pid
python modules/telegram.py & echo $! >> pid
python Web_app.py & echo $! >> pid
