#!/bin/bash

python3 manage.py makemigrations

rm -rf db/migrations

python3 manage.py migrate --run-syncdb --noinput

mkdir -p /var/www/static

chmod -R 755 /var/www

chown -R www-data:www-data /var/www

python3 manage.py collectstatic --noinput

python3 manage.py runserver 0.0.0.0:8000
