"""Read the catalog export as data. Never execute SQL from an input file."""
import json
import re
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db import models, transaction
from django.utils import timezone

TABLES = {
    'backbonetable', 'parttable', 'plasmidneed', 'straintable',
    'backbone_culture_functions', 'backbonefeaturetable', 'backbonescartable',
    'parentbackbonetable', 'parentparttable', 'parentplasmidtable',
    'partfeaturetable', 'partrputable', 'partscartable',
    'plasmid_culture_functions', 'plasmidfeaturetable', 'plasmidscartable',
    'strain_genotype_table', 'tb_backbone_userfileaddress',
    'tb_part_userfileaddress', 'tb_plasmid_userfileaddress',
}
HEADER = re.compile(r'^INSERT INTO `([\w]+)` \(([^\n]+)\) VALUES\s*', re.M)
TOKEN = re.compile(r"\s*(NULL|[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|0x[0-9a-fA-F]+)\s*(?=[,)])")


def read_rows(text):
    """Accept only literal VALUES lists from the bundled MySQL dump format."""
    end = 0
    escapes = {'0': '\0', 'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'Z': '\x1a'}
    for header in HEADER.finditer(text):
        if header.start() < end:
            continue
        table = header[1].lower()
        columns = re.findall(r'`([\w]+)`', header[2])
        if not columns or len(columns) != len(set(c.lower() for c in columns)):
            raise CommandError('Invalid INSERT columns')
        i = header.end()
        while True:
            while text[i].isspace(): i += 1
            if text[i] != '(':
                raise CommandError('Expected literal VALUES row')
            i += 1
            values = []
            while True:
                while text[i].isspace(): i += 1
                if text[i] == "'":
                    i += 1
                    value = []
                    while i < len(text):
                        char = text[i]; i += 1
                        if char == '\\':
                            char = text[i]; i += 1
                            value.append(escapes.get(char, char))
                        elif char == "'":
                            if i < len(text) and text[i] == "'":
                                value.append("'"); i += 1
                            else:
                                break
                        else:
                            value.append(char)
                    else:
                        raise CommandError('Unterminated SQL string')
                    values.append(''.join(value))
                else:
                    match = TOKEN.match(text, i)
                    if not match:
                        raise CommandError('Only SQL literals are supported')
                    literal = match[1]; i = match.end()
                    values.append(None if literal == 'NULL' else
                                  bytes.fromhex(literal[2:]) if literal.startswith('0x') else
                                  Decimal(literal) if any(c in literal for c in '.eE') else int(literal))
                while text[i].isspace(): i += 1
                separator = text[i]; i += 1
                if separator == ')': break
                if separator != ',': raise CommandError('Invalid VALUES separator')
            if len(columns) != len(values): raise CommandError('Column/value count mismatch')
            yield table, dict(zip(columns, values))
            while text[i].isspace(): i += 1
            separator = text[i]; i += 1
            if separator == ';':
                end = i
                break
            if separator != ',': raise CommandError('Unsupported SQL after VALUES')


def import_catalog(text, dry_run=False):
    catalog = {m._meta.db_table.lower(): m for m in apps.get_app_config('WebDatabase').get_models()
               if m._meta.managed and m._meta.db_table.lower() in TABLES}
    rows = {name: [] for name in catalog}
    skipped = {}
    try:
        for table, row in read_rows(text):
            if table not in catalog:
                skipped[table] = skipped.get(table, 0) + 1
                continue
            model = catalog[table]
            fields = {f.column.lower(): f for f in model._meta.concrete_fields}
            data = {}
            for column, value in row.items():
                field = fields.get(column.lower())
                if field is None:
                    raise CommandError(f'Unknown catalog column: {table}.{column}')
                if isinstance(field, models.JSONField) and isinstance(value, str): value = json.loads(value)
                # Legacy feature tables used NULL for an absent grouping label.
                if column.lower() == 'feature_group' and table.endswith('featuretable') and value is None:
                    value = ''
                value = field.to_python(value)
                if isinstance(field, models.DateTimeField) and value and settings.USE_TZ and timezone.is_naive(value):
                    # The dump explicitly sets MySQL time_zone to UTC.
                    value = timezone.make_aware(value, dt_timezone.utc)
                if value is None and not field.null:
                    raise CommandError(f'NULL is not allowed: {table}.{column}')
                if isinstance(value, str) and field.max_length and len(value) > field.max_length:
                    raise CommandError(f'Value exceeds model length: {table}.{column}')
                data[field.attname] = value
            rows[table].append(model(**data))
    except (IndexError, ValueError, ValidationError) as exc:
        raise CommandError('Invalid catalog data; no rows imported') from exc
    if not any(rows.values()): raise CommandError('No catalog rows found')
    with transaction.atomic():
        for table, model in catalog.items():
            if model.objects.exists():
                raise CommandError(f'Catalog must be empty: {table}; use a separate empty database')
        pending = {table for table, records in rows.items() if records}
        done = set(catalog) - pending
        while pending:
            ready = [table for table in pending if all(
                not f.is_relation or f.remote_field.model._meta.db_table.lower() in done
                for f in catalog[table]._meta.concrete_fields)]
            if not ready: raise CommandError('Unresolved catalog table dependencies')
            for table in sorted(ready):
                catalog[table].objects.bulk_create(rows[table], batch_size=100)
                done.add(table); pending.remove(table)
        # Check deferred constraints before rolling back a dry run, too.
        from django.db import connection
        connection.check_constraints(table_names=[catalog[t]._meta.db_table for t in rows])
        if dry_run: transaction.set_rollback(True)
    return {table: len(records) for table, records in rows.items()}, skipped
