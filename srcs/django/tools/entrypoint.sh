#!/bin/bash

python3 manage.py makemigrations

python3 manage.py migrate

mkdir -p /var/www/static

chmod -R 755 /var/www

chown -R www-data:www-data /var/www

echo "yes" | python3 manage.py collectstatic

python3 manage.py runserver 0.0.0.0:8000
