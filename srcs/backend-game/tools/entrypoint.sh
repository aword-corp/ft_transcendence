#!/bin/bash

python3 manage.py makemigrations

rm -rf db/migrations

python3 manage.py runserver 0.0.0.0:8000
