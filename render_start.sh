#!/usr/bin/env bash

python manage.py collectstatic --noinput
python manage.py migrate --noinput
daphne -b 0.0.0.0 -p $PORT UserCompte.asgi:application