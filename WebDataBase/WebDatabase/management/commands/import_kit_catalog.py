from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from WebDatabase.catalog_import import import_catalog


class Command(BaseCommand):
    help = 'Import catalog literals into an empty migrated database; never execute dump SQL.'

    def add_arguments(self, parser):
        parser.add_argument('sql_file', type=Path)
        parser.add_argument('--dry-run', action='store_true', help='Validate inserts and roll back all rows')

    def handle(self, *args, **options):
        try:
            text = options['sql_file'].read_text(encoding='utf-8-sig')
            counts, skipped = import_catalog(text, options['dry_run'])
        except (OSError, DatabaseError) as exc:
            raise CommandError('Catalog import failed; transaction rolled back. Check migrations and target schema.') from exc
        for table, count in sorted(counts.items()):
            self.stdout.write(f'{table}: {count}')
        self.stdout.write(f'Skipped non-catalog tables: {skipped}')
        self.stdout.write('Dry run rolled back' if options['dry_run'] else 'Catalog imported')
