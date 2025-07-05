#!/usr/bin/env bash

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "🔧 Application des migrations..."
python manage.py migrate --noinput

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "🚀 Lancement de Daphne..."
daphne -b 0.0.0.0 -p $PORT UserCompte.asgi:application
