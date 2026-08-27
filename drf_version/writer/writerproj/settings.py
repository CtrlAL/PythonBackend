import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "dev-insecure-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth", "rest_framework", "links"]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "writerproj.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": False, "OPTIONS": {}}]
WSGI_APPLICATION = "writerproj.wsgi.application"
DATABASES = {}
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SCYLLA_HOSTS = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
BASE_URL = os.environ.get("BASE_URL", "http://localhost")
