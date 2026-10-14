"""Isolated test configuration, including offline API endpoints."""
import os

os.environ.update(SECRET_KEY='isolated-tests-not-for-deployment', DEBUG='False',
    ALLOWED_HOSTS='testserver,localhost', SQLITE_PATH=':memory:',
    WEBDATABASE_URL='http://localhost:8000/WebDatabase/',
    LABDATABASE_URL='http://localhost:8000/LabDatabase/',
    API_LOGIN_USERNAME='', API_LOGIN_PASSWORD='', API_LOGIN_URL='')
from .settings import *  # noqa: E402,F403
