to init a hardware:

sudo systemctl daemon-reload

dosctl restart/start

check if everything is running okay:

doslogs -f

check is whether the application is running:

ps aux | grep python

dosctl status
