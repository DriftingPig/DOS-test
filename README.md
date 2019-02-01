to init a hardware:

sudo systemctl daemon-reload

dosctl restart/start

check if everything is running okay:

doslogs -f

check is whether the application is running:

ps aux | grep python

dosctl status



example of running a script with an architect:

python LUT.py --role LUT-TEST --device_mode True --service DOStest

architect -i HUI-TEST -c console.ini

join_instance HUI-TEST
