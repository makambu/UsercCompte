#!/usr/bin/env bash

# Lire le port depuis l'environnement (Render)
export PORT=${PORT:-8000}

# Lancer Daphne sur le bon port
exec daphne -b 0.0.0.0 -p $PORT UserCompte.asgi:application