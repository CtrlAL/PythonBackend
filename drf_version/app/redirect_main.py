import os

import django
from django.conf import settings


settings.configure(
    DEBUG=os.environ.get("DEBUG", "True") == "True",
    ALLOWED_HOSTS=["*"],
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-insecure-key-redirect"),
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    MIDDLEWARE=["django.middleware.common.CommonMiddleware"],
    ROOT_URLCONF="app.redirect_urls",
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {},
        }
    ],
    WSGI_APPLICATION="app.redirect_main.application",
    DATABASES={},
    LANGUAGE_CODE="en-us",
    TIME_ZONE="UTC",
    STATIC_URL="/static/",
    DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
)

django.setup()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
