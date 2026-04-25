import os
import sys
from django.core.wsgi import get_wsgi_application

# Ensure Django project package is importable on Vercel.
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DJANGO_ROOT = os.path.join(PROJECT_ROOT, "mysite")
if DJANGO_ROOT not in sys.path:
    sys.path.insert(0, DJANGO_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
app = get_wsgi_application()
