"""Run from WebDataBase: python tests/test_migrations.py -v.

Uses only in-memory SQLite; never loads deployment settings or .env.
This checks schema bootstrap, not API behavior or existing MySQL upgrades.
"""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from django.conf import settings

settings.configure(
    SECRET_KEY='migration-tests-only',
    INSTALLED_APPS=[
        'django.contrib.auth', 'django.contrib.contenttypes',
        'django.contrib.sessions', 'django.contrib.admin', 'WebDatabase',
    ],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    AUTH_USER_MODEL='WebDatabase.CustomUser',
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    USE_TZ=True,
)

import django
django.setup()
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class MigrationBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        call_command('migrate', verbosity=0, interactive=False, skip_checks=True)

    def test_all_managed_tables_and_columns_exist(self):
        tables = set(connection.introspection.table_names())
        with connection.cursor() as cursor:
            for model in apps.get_app_config('WebDatabase').get_models(include_auto_created=True):
                if not model._meta.managed:
                    continue
                with self.subTest(model=model.__name__):
                    self.assertIn(model._meta.db_table, tables)
                    columns = {c.name for c in connection.introspection.get_table_description(cursor, model._meta.db_table)}
                    self.assertTrue({f.column for f in model._meta.local_fields} <= columns)

    def test_custom_user_and_business_foreign_keys(self):
        with connection.cursor() as cursor:
            for name in ('UserProfile', 'Partfeaturetable', 'Plasmidfeaturetable', 'Backbonefeaturetable'):
                model = apps.get_model('WebDatabase', name)
                constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
                actual = {c['foreign_key'] for c in constraints.values() if c['foreign_key']}
                expected = {(f.target_field.model._meta.db_table, f.target_field.column)
                            for f in model._meta.local_fields if f.is_relation and f.db_constraint}
                with self.subTest(model=name):
                    self.assertTrue(expected <= actual)

    def test_no_model_changes_missing_from_migrations(self):
        call_command('makemigrations', 'WebDatabase', dry_run=True, check=True,
                     verbosity=0, skip_checks=True)

    def test_repeated_migrate_preserves_data(self):
        User = apps.get_model('WebDatabase', 'CustomUser')
        user = User.objects.create(username='migration-test', uname='migration-test', password='!')
        before = set(MigrationRecorder(connection).applied_migrations())
        call_command('migrate', verbosity=0, interactive=False, skip_checks=True)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertEqual(before, set(MigrationRecorder(connection).applied_migrations()))


if __name__ == '__main__':
    unittest.main()
