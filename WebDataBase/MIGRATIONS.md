# Database migrations

`WebDatabase/migrations/0001_initial.py` defines the current model baseline.
Commit this file together with model changes and migration tests. Keep subsequent
schema changes in new migrations rather than regenerating an applied baseline.

## Fresh empty database

Configure `WebDataBase/.env` for a **new empty MySQL database**, then run from
`WebDataBase`:

```text
python manage.py migrate --plan
python manage.py migrate
python manage.py makemigrations --check --dry-run
```

`manage.py` selects `WebDataWorld.settings` automatically. The initial migration
creates Django-managed business tables, including parts, backbones, plasmids,
features, provenance, visitors and the custom user. Standard Django migrations
create their own system tables. It does not seed component data.

The 20 models explicitly declared `managed=False` remain unmanaged. They include
legacy mirrors of Django tables and historical datasets such as `gates`, `parts`,
`structures` and `yeastparts`. Their migration state is recorded, but Django does
not create or maintain those tables. Restore the relevant historical schema/data
before using features that depend on those datasets; do not turn all these models
into managed models because some mirror tables owned by Django itself.

## Existing databases

Back up both data and `django_migrations` before planning an upgrade. Inspect
`python manage.py showmigrations WebDatabase` and the actual tables/columns.

- A database that already recorded an **empty** `0001_initial` will not execute
  the rebuilt migration just because the file changed.
- A database with the former `0002`–`0004` history needs reconciliation against
  that exact deployed history. Do not delete migration records or recreate tables
  as a general repair.
- `--fake-initial` only detects table/column existence; it does not prove that
  existing types, indexes or constraints match. It is not suitable for a partial
  import where only some tables from this initial migration already exist.

No existing deployment database is modified by the regression checks below.

## Bundled KitAssembly SQL

`../KitAssembly_Labdnadata_20260923_072954.sql` is a MySQL 8 catalog subset with
both `CREATE TABLE` and `INSERT` statements. It is not a full deployment backup
and does not contain the complete Django application schema or migration history.

After `migrate` on a fresh database, use the data-only importer from `WebDataBase`:

```text
python manage.py import_kit_catalog ../KitAssembly_Labdnadata_20260923_072954.sql --dry-run
python manage.py import_kit_catalog ../KitAssembly_Labdnadata_20260923_072954.sql
python manage.py create_kit_service_user kit-service
```

This command parses literal INSERT values for 20 catalog tables; no SQL from the
input file is executed. IDs and foreign keys are preserved. Historical task/result
rows and account data are excluded. NULL `feature_group` values are mapped to the
current model's empty-string representation; other incompatible values are rejected.
Dry runs roll back. All target catalog tables must be empty; repeated imports are
refused without changing existing rows. Import failures roll back the transaction.

The bundled snapshot provides 2,507 catalog/related rows (84 parts, 76 backbones,
109 plasmids). Four requested backbones were absent when it was exported; no data
is invented for them. The importer does not replace an upgrade procedure for an
existing database and does not create unmanaged tables. Never run the dump's DDL
in a migrated database or use `--fake-initial` as a substitute for schema comparison.

## Regression checks

From `WebDataBase`:

```text
python tests/test_migrations.py -v
```

The tests use in-memory SQLite with minimal settings, never `.env` or deployment
database credentials. They verify creation of all managed tables/columns, selected
business/custom-user foreign keys, no missing model migrations, and repeated
`migrate` preserving data. The separate API suite and catalog importer tests run on SQLite and MySQL in CI.
