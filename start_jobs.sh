redis-server & echo $! > pid
sudo python3 Badge.py & echo $! >> pid
python Web_app.py & echo $! >> pid
