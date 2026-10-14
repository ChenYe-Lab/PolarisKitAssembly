import getpass
import hashlib
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from WebDatabase.models import CustomUser


class Command(BaseCommand):
    help = 'Create an editor service account without Django admin privileges.'

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']
        if CustomUser.objects.filter(username=username).exists() or CustomUser.objects.filter(uname=username).exists():
            raise CommandError('Account already exists; no changes made')
        password = getpass.getpass('Password: ')
        if password != getpass.getpass('Password again: '):
            raise CommandError('Passwords do not match')
        user = CustomUser(username=username, uname=username, role='editor', is_staff=False, is_superuser=False)
        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc
        # Match the existing account form's legacy preprocessing, then use Django's hasher.
        user.set_password(hashlib.md5(password.encode('utf-8')).hexdigest())
        user.save()
        self.stdout.write('Service account created; configure frontend API_LOGIN_USERNAME/API_LOGIN_PASSWORD.')
