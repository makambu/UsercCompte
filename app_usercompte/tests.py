from django.test import TestCase

# Create your tests here.

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UserCompte.settings')
django.setup()
