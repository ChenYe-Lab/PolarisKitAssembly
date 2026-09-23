import requests
from django.conf import settings


class ApiSession(requests.Session):
    """Apply the configured timeout to every downstream request."""
    def request(self, method, url, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = settings.API_REQUEST_TIMEOUT
        return super().request(method, url, **kwargs)
