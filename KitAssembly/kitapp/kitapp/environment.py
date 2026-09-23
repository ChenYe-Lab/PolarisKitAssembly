"""Validated deployment settings. This module does not read files or secrets."""
import math
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def build_configuration(base_dir, env):
    def text(name, default=''):
        return str(env.get(name, default)).strip()

    def boolean(name, default=False):
        value = text(name, str(default)).lower()
        if value in {'1', 'true', 'yes', 'on'}:
            return True
        if value in {'0', 'false', 'no', 'off'}:
            return False
        raise ImproperlyConfigured(f'{name} must be a boolean')

    def positive(name, default, cast=int):
        try:
            value = cast(text(name, default))
            if value <= 0 or not math.isfinite(value):
                raise ValueError()
            return value
        except (ValueError, TypeError, OverflowError):
            raise ImproperlyConfigured(f'{name} must be a positive number') from None

    def items(name, default=''):
        return [item.strip() for item in text(name, default).split(',') if item.strip()]

    def url(name, default='', base=False):
        value = text(name) or default
        try:
            parts = urlsplit(value)
            valid = (parts.scheme in ('http', 'https') and parts.hostname and
                     not parts.username and not parts.password and not parts.query and
                     not parts.fragment and not any(c.isspace() for c in value))
            parts.port  # Validate a supplied port without displaying credentials.
        except ValueError:
            valid = False
        if not valid:
            raise ImproperlyConfigured(f'{name} must be an absolute HTTP(S) URL without credentials, query or fragment')
        return value.rstrip('/') + '/' if base else value

    def path(name, default='', legacy=None):
        value = text(name) or (text(legacy) if legacy else '') or default
        if not value:
            return None
        result = Path(value).expanduser()
        return result if result.is_absolute() else Path(base_dir) / result

    secret = text('SECRET_KEY')
    if not secret or secret == 'replace-with-your-secret-key':
        raise ImproperlyConfigured('SECRET_KEY must be set to a unique secret')
    debug = boolean('DEBUG')
    hosts = items('ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]')
    if not hosts:
        raise ImproperlyConfigured('ALLOWED_HOSTS must contain at least one host')
    web_url = url('WEBDATABASE_URL', base=True)
    lab_url = url('LABDATABASE_URL', base=True)
    username = text('API_LOGIN_USERNAME')
    # Do not strip passwords: surrounding spaces can be intentional.
    password = env.get('API_LOGIN_PASSWORD', '')
    if bool(username) != bool(password):
        raise ImproperlyConfigured('Set both API_LOGIN_USERNAME and API_LOGIN_PASSWORD, or leave both empty')
    same_site = text('VISITOR_COOKIE_SAMESITE', 'Lax')
    same_site = {'lax': 'Lax', 'strict': 'Strict', 'none': 'None'}.get(same_site.lower())
    if same_site is None:
        raise ImproperlyConfigured('VISITOR_COOKIE_SAMESITE must be Lax, Strict or None')
    visitor_secure = boolean('VISITOR_COOKIE_SECURE', not debug)
    if same_site == 'None' and not visitor_secure:
        raise ImproperlyConfigured('VISITOR_COOKIE_SAMESITE=None requires VISITOR_COOKIE_SECURE=True')
    csrf_origins = items('CSRF_TRUSTED_ORIGINS')
    for origin in csrf_origins:
        try:
            parsed = urlsplit(origin)
            valid = (parsed.scheme in ('http', 'https') and parsed.hostname and
                     not parsed.username and not parsed.password and parsed.path in ('', '/') and
                     not parsed.query and not parsed.fragment and not any(c.isspace() for c in origin))
            parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS must contain HTTP(S) origins')
    return {
        'SECRET_KEY': secret, 'DEBUG': debug, 'ALLOWED_HOSTS': hosts,
        'CSRF_TRUSTED_ORIGINS': csrf_origins,
        'SESSION_COOKIE_SECURE': boolean('SESSION_COOKIE_SECURE', not debug),
        'CSRF_COOKIE_SECURE': boolean('CSRF_COOKIE_SECURE', not debug),
        'WEBDATABASE_URL': web_url, 'LABDATABASE_URL': lab_url,
        'API_LOGIN_URL': url('API_LOGIN_URL', web_url + 'login'),
        'API_LOGIN_USERNAME': username, 'API_LOGIN_PASSWORD': password,
        'API_LOGIN_USERNAME_FIELD': text('API_LOGIN_USERNAME_FIELD') or 'username',
        'API_LOGIN_PASSWORD_FIELD': text('API_LOGIN_PASSWORD_FIELD') or 'password',
        'API_LOGIN_NEXT': text('API_LOGIN_NEXT'),
        'API_REQUEST_TIMEOUT': positive('API_REQUEST_TIMEOUT', 20, float),
        'VISITOR_COOKIE_NAME': text('VISITOR_COOKIE_NAME') or 'kitapp_visitor_id',
        'VISITOR_COOKIE_MAX_AGE': positive('VISITOR_COOKIE_MAX_AGE', 60 * 60 * 24 * 365),
        'VISITOR_COOKIE_SECURE': visitor_secure, 'VISITOR_COOKIE_SAMESITE': same_site,
        'TUTORIAL_ADDRESS': path('TUTORIAL_ADDRESS', legacy='TUROERIAL_ADDRESS'),
        'ZIP_ADDRESS': path('ZIP_ADDRESS'),
        'TUTORIAL_SITE_ROOT': path('TUTORIAL_SITE_ROOT', 'site'),
        'SQLITE_PATH': path('SQLITE_PATH', 'db.sqlite3'),
    }
