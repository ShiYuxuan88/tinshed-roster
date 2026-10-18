# The Tinshed Players crew roster

A small web application for a fictional community theatre. It keeps productions, performances, volunteers, and crew assignments in one place. This ISYS3001 A3 team delivery builds on the A2 prototype; names in the demo seed are fictional. The canonical submission repository is [ShiYuxuan88/tinshed-roster](https://github.com/ShiYuxuan88/tinshed-roster).

## Capabilities

- Create and edit volunteers, productions, and performances.
- Assign, change, and remove a volunteer's role on a performance roster.
- Prevent the same role or volunteer being assigned twice to one performance.
- Mark or clear an assignment's confirmation. Changing its volunteer or role resets confirmation to Pending; saving unchanged details preserves it. This is a coordinator's record, not authenticated volunteer consent.
- View a volunteer's personal roster, including an empty state.
- Persist records in SQLite and check application health at `/health`.

The prototype has no user accounts or role permissions. Use fictional data only. It is not suitable for managing real volunteer contact details on a public deployment.

## Local setup

Requires Python 3.12 or newer. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:APP_ENV = 'development'
$env:SECRET_KEY = 'a-local-only-random-value'
.\.venv\Scripts\python.exe -m flask --app app run --port 8000
```

Open `http://127.0.0.1:8000`. On macOS or Linux, use `python3 -m venv .venv`, `.venv/bin/python`, and `export` for environment variables. The SQLite file is created on first start under `instance/` by default. Set `APP_DATABASE` to use another path. A fictional sample can be added to an empty database with:

```powershell
.\.venv\Scripts\python.exe -m flask --app app seed-demo
```

Run automated checks with `.\.venv\Scripts\python.exe -m pytest -q`.
`pytest.ini` limits default collection to `tests/`, excluding temporary local review copies. These checks use Flask's test client and SQLite; they do not constitute browser automation. See [the delivery guide](docs/A3_DELIVERY.md) for provenance, release checks and a manual demo checklist.

## Configuration and deployment

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | `development` or `production` | `development` |
| `APP_DATABASE` | SQLite file path | `instance/tinshed.sqlite3` |
| `SECRET_KEY` | Signs form sessions | Local-only fallback; required in production |
| `PORT` | Local direct-run port | `8000` |

Do not commit `.env`, SQLite databases, or secrets. Copy `.env.example` only as a starting checklist and set real values in the environment. For a production-style local WSGI run, set `APP_ENV=production` and a strong `SECRET_KEY`, then use:

```powershell
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 app:app
```

`Dockerfile` and `.github/workflows/ci.yml` provide repeatable build and test configuration. CI runs pytest, builds the production image, checks `/health`, seeds fictional data and verifies it after container removal and recreation with the same mounted database. The database needs a persistent writable volume outside the container; the image uses `/data/tinshed.sqlite3`. Consult the Actions run for the exact commit before claiming this gate passed. It does not verify cloud deployment or backup restoration. HTTPS, authentication, backups, and access control are not implemented; keep demonstrations local with fictional data.

## Project layout

- `app.py`: Flask routes, SQLite schema, validation, and app factory.
- `templates/`: web pages for each workflow.
- `static/`: responsive styles.
- `tests/`: focused workflow and data integrity tests.
- `Dockerfile`: deployment packaging.
- `.github/workflows/ci.yml`: automated test gate.
- `A2_HD_Execution_Plan.md`: scope and assessment evidence plan.

## Known limitations and next steps

The starter case also mentions ticketing, memberships, SMS, equipment inventory, reports, and volunteer availability. These are outside this roster prototype. Authentication, granular permissions, availability checks, authenticated volunteer responses and backup/restore remain future work before real use. The existing confirmation button does not provide these safeguards.
