# Publication-fix validation — 2026-10-14

Local validation used Python 3.14, Django 5.2.4, MySQL 8.0.36 and Node.js 20.
No deployment database was queried or changed. MySQL ran in a disposable data
directory bound to localhost and was stopped after each run.

| Check | Result |
| --- | --- |
| Backend API/configuration/annotation/security/catalog tests, SQLite | 58 passed |
| Same backend suite, isolated MySQL | 58 passed |
| Frontend configuration/feedback/service-login tests | 21 passed |
| Migration bootstrap/consistency tests | 4 passed |
| HTML escaping and actual card-renderer regression | 2 passed |

The backend suite includes a real HTTP login from the frontend's requests session,
followed by a CSRF-protected repository write. It tests anonymous/forged-session
rejection, reader write denial, wrong passwords, inactive accounts and log redaction.
Catalog tests migrate a fresh schema, dry-run and import the bundled snapshot,
verify 2,507 imported rows, skip 8 historical task/result rows, refuse repeated
imports, and verify rollback. These checks are not a full browser workflow test
or a validation of every biological assembly result.

GitHub Actions is configured for Python 3.12, SQLite, MySQL 8 and Node.js 22.
The workflow has not yet run on GitHub; the table reports local runs only.

Remaining earlier audit items outside this change: credential rotation/history
cleanup, public administrator registration, and unauthenticated password-reset
behavior. They still prevent treating this checkout as ready for public deployment.
