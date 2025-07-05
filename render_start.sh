#!/usr/bin/env bash

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

python manage.py migrate --noinput
daphne -b 0.0.0.0 -p $PORT UserCompte.asgi:application