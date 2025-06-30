#!/usr/bin/env bash
# Script de build pour Render

# Arrêt si erreur
set -o errexit

# Installations des dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Application des migrations
python manage.py migrate
