#!/usr/bin/env bash

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "🗃️ Migration de la base de données..."
python manage.py migrate --noinput