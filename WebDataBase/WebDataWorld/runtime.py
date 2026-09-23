"""Shared policies used by views and background workers."""
from pathlib import Path
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured


def service_url(setting, endpoint=''):
    base = getattr(settings, setting, '').strip()
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ImproperlyConfigured(f'{setting} must be an absolute HTTP(S) URL')
    return base.rstrip('/') + '/' + endpoint.lstrip('/')


class ServiceSession(requests.Session):
    """Bound every outbound request; preserve Requests' exception contract."""
    def request(self, method, url, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = settings.SERVICE_HTTP_TIMEOUT
        return super().request(method, url, **kwargs)


def service_get(url, **kwargs):
    with ServiceSession() as session:
        return session.get(url, **kwargs)


def set_task_status(key, value):
    return cache.set(key, value, timeout=settings.TASK_STATUS_TTL_SECONDS)


def output_file(directory, filename):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if Path(filename).name != filename or '/' in filename or '\\' in filename:
        raise ValueError('Expected a filename without directory components')
    return str(directory / filename)


def page_size(value=None, *, upload=False):
    default = settings.UPLOAD_PAGE_SIZE if upload else settings.API_PAGE_SIZE
    maximum = settings.UPLOAD_MAX_PAGE_SIZE if upload else settings.API_MAX_PAGE_SIZE
    return min(max(int(value or default), 1), maximum)
