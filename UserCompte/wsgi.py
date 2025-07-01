import os
from whitenoise import WhiteNoise
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UserCompte.settings')

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent  # Ajoute ceci

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'staticfiles'))
