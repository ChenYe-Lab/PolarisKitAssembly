# Hardcoding cleanup validation

Validated with Python 3.14 and Django 5.2.4, using isolated SQLite databases.
No production database or external service was contacted.

- New configuration/design tests: 18 passed.
- Assembly annotation/persistence tests: 17 passed, including a real assembly.
- Combined API/configuration suite: 31 tests, 23 passed and 8 existing failures.
  The original source copy reproduces the identical 8 failures (13 API tests,
  5 passed). No additional API failure was introduced.
- Django system checks: passed.
- Python sources: parsed with Python 3.10 grammar compatibility checking.

Existing API failures, outside the hardcoding cleanup:

1. Part, Backbone and Plasmid flow tests expect obsolete string responses,
   while the current views return `{"success": true}` (3 failures).
2. Repository test sets only session metadata; the view requires an authenticated
   `request.user` (1 failure).
3. Backbone scar missing/empty ID errors access an unset `error_code` field
   in `WebDatabaseValidationException` (2 errors).
4. Backbone scar not-found/wrong-method status assertions disagree with the
   current response behavior (2 failures).

The original migration chain also fails on a removed `customparentinformation`
field. `WebDataWorld.test_settings` disables application migrations for the API
tests and creates the current model schema. The existing feature migration test
is still exercised by the standalone assembly test suite. Production migrations
were neither modified nor executed.

Deployment-specific service reachability and measurements cannot be validated
without the deployment's configuration/data. See `CONFIGURATION.md` before
switching artifact paths or enabling recommendations.
