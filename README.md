# Intro
Muddery is an online text game (like MUD) framework in Python. It is licensed under 3-clause BSD license.


# Installation
1. Install Python3.7+ and GIT. Start a Console/Terminal.
1. `cd` to some place you want to do your development. 
1. `git clone https://github.com/muddery/muddery`
1. `python -m venv mudenv`
1. `source mudenv/bin/activate` (Linux, Mac) or `mudenv\Scripts\activate` (Windows) //执行以后，关闭终端，重新打开一个新的终端
1. `pip install -e muddery` #挂梯子执行
1. `muddery --init mygame` //初始化
1. `cd mygame`
1. `muddery setup`
1. `muddery start`

Muddery should now be running and you can connect to it by pointing your web browser to http://localhost:8000.

If you want to stop the server, you can use `muddery stop`.

![例图1](./img/1.png)

![例图2](./img/2.png)

![例图3](./img/3.png)
