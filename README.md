# char.bot.demo
A demonstrator for the Fuzzy Conversational Character Computing (FCCC) framework.

This demonstrator is built on a flask application. Either you can run it on your local machine using the localhost or you setup a flask server (see instructions below). You can **start** the app with the script app.py.

The demonstrator relies on multiple chatbot backends that are implemented using the GPT API. Consequently, you need to get a personalized API-Key that must be set within the __init__ method of CBotGPT class (see CBotGPT.py script).

Here is a short guide how to install a flask server:
1. create debian/ubuntu instance
2. install server
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
        sudo apt update
        sudo apt install caddy
3. install python
        sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
        sudo apt install python3-venv
4. install gunicorn in venv            # used to run flask app
        sudo apt install gunicorn
5. add Caddyfile to project (root folder)
        > filename: Caddyfile
        > minimum content: http://ipOfServer { reverse_proxy localhost:8000 }
        > you can see port when app started with gunicorn from terminal:
                gunicorn app:app        # filename (app.py):appname (app = Flask(__name__))
6. update caddy config
        > caddy stop
        > sudo caddy start              # in the directory with the "Caddyfile" config file
7. send app start process to background with terminating $ sign
        gunicorn app:app &
