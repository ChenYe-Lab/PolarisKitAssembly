"""Isolated SQLite settings: python manage.py test --settings=WebDataWorld.test_settings"""
import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'isolated-test-key-not-for-deployment')
from .settings import *  # noqa: E402,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
# Legacy migration 0003 removes a field absent from its migration state.
# These API tests exercise the current models; migration tests run separately.
MIGRATION_MODULES = {'WebDatabase': None, 'LabDatabase': None}
LOGGING = {}
ALLOWED_HOSTS = ['testserver', 'localhost']
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
