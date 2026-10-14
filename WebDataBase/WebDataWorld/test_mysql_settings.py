"""CI-only disposable MySQL database; explicit TEST_MYSQL_* variables required."""
import os
from .test_settings import *  # noqa: F403

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': os.environ['TEST_MYSQL_DATABASE'],
    'USER': os.environ['TEST_MYSQL_USER'],
    'PASSWORD': os.environ['TEST_MYSQL_PASSWORD'],
    'HOST': os.environ['TEST_MYSQL_HOST'],
    'PORT': os.environ['TEST_MYSQL_PORT'],
    'OPTIONS': {'charset': 'utf8mb4'},
}}
