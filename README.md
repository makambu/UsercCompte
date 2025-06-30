# CGM_App - Application de gestion communautaire

Ce projet est une plateforme Django permettant aux utilisateurs de :
- Créer un compte avec image de profil
- Poster des blogs et vidéos
- Commenter et aimer les publications
- Suivre les activités via un système de notifications
- Profiter d’une expérience interactive en AJAX
- Gérer les profils utilisateurs

## 🔧 Technologies utilisées
- Python / Django
- HTML / CSS / Bootstrap
- JavaScript (AJAX)
- MySQL ou SQLite (dev)
- Git / GitHub

## 📦 Installation

```bash
git clone https://github.com/makambu/UsercCompteCgm.git
cd UsercCompteCgm
python -m venv venv
venv\Scripts\activate    # sur Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
