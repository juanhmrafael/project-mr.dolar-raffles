import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "apps"))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.production"),
)

application = get_wsgi_application()
