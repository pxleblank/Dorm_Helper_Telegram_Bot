#!/bin/bash

python3.11 manage.py runserver
sleep 5
python3.11 bot/main.py