# Deployment configuration

Copy `.env.example` to `.env` only for a new installation. Keep existing secrets.
Set a unique `DJANGO_SECRET_KEY`; an absent key or the example placeholder now
fails startup. Production defaults to `DJANGO_DEBUG=False`, localhost-only hosts,
secure cookies and no extra CSRF origins. Explicitly configure your deployment.
Environment variables override `.env`.

## Services and files

Set `WEBDATABASE_API_BASE_URL` to the reachable WebDatabase API and
`EXPERIMENT_BASE_URL` to the experiment service. All application HTTP sessions
use `SERVICE_HTTP_TIMEOUT`; failures retain the Requests exception contract.
Missing experiment configuration fails only when that feature is requested.

Generated artifacts now default to `media/assembly`, `media/assembly_inputs`
and `media/generated`. Excel templates remain bundled static resources.
All generators, download views and diagram views use the same settings.
To continue serving old artifacts, configure the new directory variables to
their existing locations, or copy the artifacts before switching directories.
Do not delete the old files. Existing custom scar data can be retained by setting
`CUSTOM_SCAR_FILE` to its current location. New installations use
`media/CustomScarInfo.txt`. See `.env.example` for all path overrides.

## Design data

Copy `WebDataWorld/design_config.example.json` to a deployment-owned JSON file
and set `DESIGN_CONFIG_FILE`. The example preserves the two known backbone names
but deliberately contains no fabricated strengths. Example entry syntax:

```json
{
  "backbones": {"ecoli": "pEcBb15", "yeast": "pScBb04"},
  "part_strengths": {
    "123": {"value": 20.0, "source": "demo assumption; replace with verified data"}
  }
}
```

`123` is an illustrative PartID, not a shipped assignment. Populate entries for
the actual promoter, RBS and terminator IDs with values and provenance. Missing
data gives an explicit error; no strength is assigned according to name order.
Renaming a part does not change its strength. Repository metadata retains the
selected IDs, strengths and sources. Add explicit Bacillus/Mammalian backbone
mapping before enabling recommendations for those chassis. Unknown chassis
never falls back to a yeast backbone. Restart workers after editing design data.

Legacy part type IDs remain 1=promoter, 2=CDS, 3=terminator, 4=RBS, centralized
in `WebDatabase.part_types.PartType`; existing data needs no renumbering.

## Runtime policies

All task progress writes refresh `TASK_STATUS_TTL_SECONDS`, avoiding accidental
expiry after an intermediate update. Configure a shared Django cache backend
when using multiple processes; this change does not add a cache service.
Database retry deadline and interval are configurable; exception eligibility is
unchanged. Creation (720h), update/renewal (24h), and design creation (720h) retain
their separate existing expiry semantics. Pagination defaults and limits have
separate settings for normal and upload listings.

## Validation

From `WebDataBase`, run the migration regression checks:

```text
python tests/test_migrations.py -v
```

These checks use an isolated in-memory SQLite database and do not load `.env`
or deployment settings. They cover managed tables/columns, key foreign keys,
model/migration consistency and preservation of data on repeated migrations.
They do not verify MySQL upgrades or replace API and assembly regression tests.
API, configuration, annotation and authentication regression sources are restored.
Run `python manage.py test WebDatabase.tests LabDatabase.tests --settings=WebDataWorld.test_settings`.
CI additionally uses `WebDataWorld.test_mysql_settings` with explicit `TEST_MYSQL_*`
variables against a disposable MySQL instance, never a deployment database.

API access now requires an active Django session. Legacy `session['info']` alone is
not authentication. Business writes require editor/manager/admin (or superuser) and
CSRF validation, including formerly exempt endpoints. Provision the frontend service
account with `python manage.py create_kit_service_user kit-service`. The frontend
obtains the backend's CSRF token, POSTs credentials and verifies the resulting session.

For fresh databases and existing migration histories, see [MIGRATIONS.md](MIGRATIONS.md).
Preserve existing databases, `.env`, generated artifacts and unrelated changes.
