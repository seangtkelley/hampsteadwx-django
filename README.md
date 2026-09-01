# Cooperative Climatological Data Explorer

A website that dynamically creates text and visual summaries of climatological information based on CSV files containing raw observation data.

![January 2016 Monthly Summary](http://seangtkelley.me/img/hampsteadwx-jan2016.png "January 2016 Monthly Summary")

Production: [hampsteadwx-django.herokuapp.com](http://hampsteadwx-django.herokuapp.com)

## Notable features

1. [Monthly Summaries](http://hampsteadwx-django.herokuapp.com/summaries/monthly/2016/12)
2. [Annual Summaries](http://hampsteadwx-django.herokuapp.com/summaries/annual/2016)
3. [Snow Season Summaries](http://hampsteadwx-django.herokuapp.com/summaries/snowseason)
4. [Sunset Lake Ice In/Ice Out](http://hampsteadwx-django.herokuapp.com/summaries/sunsetlake)

## Data Sources

- [Daily Observations](https://wxcoder.org/)
- [30-year Climate Normals](https://www.ncei.noaa.gov/access/us-climate-normals/#dataset=normals-monthly&timeframe=30)

---

## Local development

### Prerequisites

| Tool | Notes |
|------|--------|
| [uv](https://docs.astral.sh/uv/) | Python version and virtualenv management |
| PostgreSQL 14+ | **Required** to run the app and **integration** tests (ArrayField). Unit tests mock the ORM and do not query Postgres. |
| [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) | Optional; needed to pull production data |

Python **3.10.9** is pinned in `.python-version` and `runtime.txt`. Match that locally to stay aligned with Heroku.

### Database: PostgreSQL required

Summary models use PostgreSQL-only [`ArrayField`](https://docs.djangoproject.com/en/stable/ref/contrib/postgres/fields/#arrayfield) (including nested arrays for date lists). **SQLite is not supported** for this project.

### 1. Clone and create a virtual environment

```bash
git clone git@github.com:seangtkelley/hampsteadwx-django.git
cd hampsteadwx-django

uv sync
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

Dependencies are declared in `pyproject.toml`. `uv sync` installs runtime and **dev** dependencies (Ruff, ty, pytest, pytest-django, pytest-cov) from the lockfile.

If `uv sync` fails building `psycopg2`, install PostgreSQL client libraries locally (e.g. `brew install libpq` and ensure `pg_config` is on your `PATH`).

For Heroku deployment, regenerate the production lockfile export when dependencies change:

```bash
uv export --no-dev --no-hashes -o requirements.txt
```

### 2. Local PostgreSQL

Create a database and user (adjust names as you like):

```bash
# macOS (Homebrew) example
brew services start postgresql@16
createuser -s hampsteadwx_dev 2>/dev/null || true
createdb -O hampsteadwx_dev hampsteadwx_local
```

Connection URL for Django (Heroku-style, which `dj-database-url` expects):

```bash
export DATABASE_URL='postgres://hampsteadwx_dev@localhost:5432/hampsteadwx_local'
```

On Linux you may need a password in the URL, e.g. `postgres://user:password@localhost:5432/hampsteadwx_local`.

### 3. Environment variables and local settings

`boilerplate/settings.py` reads **`DATABASE_URL`** from the environment for the database (same as Heroku). **`SECRET_KEY`**, **`DEBUG`**, and **`ALLOWED_HOSTS`** come from the environment in production; locally, use `settings_secret.py` for those.

```bash
export DATABASE_URL='postgres://hampsteadwx_dev@localhost:5432/hampsteadwx_local'
```

**Recommended: `settings_secret.py` for local-only Django flags**

```bash
cp boilerplate/settings_secret.py.template boilerplate/settings_secret.py
```

The template sets `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` only — not the database. Uncomment the import at the bottom of `boilerplate/settings.py`:

```python
from .settings_secret import *
```

`settings_secret.py` is gitignored. Change the template `SECRET_KEY` if you like; never use that value in production.

**Alternative: environment only**

```bash
export SECRET_KEY='local-dev-only-change-me'
export DATABASE_URL='postgres://hampsteadwx_dev@localhost:5432/hampsteadwx_local'
```

You still need `DEBUG` and `ALLOWED_HOSTS` for comfortable local use — use `settings_secret.py` or extend `settings.py` to read them from the environment.

### 4. Migrate and run

```bash
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Optional: create a superuser for the admin site.

```bash
python manage.py createsuperuser
```

### 5. Running tests

Tests live under `tests/` and use **pytest** + **pytest-django** + **pytest-cov**. Config is in `pyproject.toml` under `[tool.pytest.ini_options]`.

| Suite | Location | What it does | Postgres? |
|-------|----------|--------------|-----------|
| **Unit** (default) | `tests/unit/` | Mocks ORM, normals files, and `render`; covers utils, views, forms, filters, `bulk_recalc` | No (not queried) |
| **Integration** | `tests/integration/` | Real ORM + HTTP client against ArrayField models | Yes |

**Unit tests** (default — no DB connection):

```bash
export SECRET_KEY='test-secret-key-not-for-production'
# Django settings still require DATABASE_URL at import time; it is not queried by unit tests.
export DATABASE_URL='postgres://hampsteadwx_dev@localhost:5432/hampsteadwx_test'

uv sync
uv run pytest
```

**Integration tests** (PostgreSQL required). Create an empty DB if needed (`createdb hampsteadwx_test`), then:

```bash
uv run pytest -m integration
```

Run both:

```bash
uv run pytest -m "unit or integration"
```

Coverage for the `api` package is enabled by default (`--cov=api`). Markers: `unit`, `integration`. Default `addopts` excludes integration (`-m "not integration"`).

Shared fixtures: `tests/conftest.py`, `tests/fixtures/sample_daily.csv`. Integration-only factories live in `tests/integration/conftest.py`.

### 6. Static files (optional locally)

Production uses WhiteNoise with compressed manifest storage. For local dev, Django serves `STATICFILES_DIRS` automatically. To mimic production:

```bash
python manage.py collectstatic --noinput
```

### Code quality

Lint, format, type-check, and test:

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
uv run pytest                 # unit
uv run pytest -m integration  # needs Postgres
```

Configuration lives in `pyproject.toml` under `[tool.ruff]`, `[tool.ty]`, and `[tool.pytest.ini_options]`.

Pull requests run the same checks via [`.github/workflows/ci.yml`](.github/workflows/ci.yml): Ruff (lint + format), `ty`, unit tests, and integration tests against a PostgreSQL 16 service.

### Management commands

Recalculate stored summaries after changing calculation logic in `api/utils.py`:

```bash
python manage.py bulk_recalc --all
python manage.py bulk_recalc -y 2020 2021
python manage.py bulk_recalc -m 1 2 -y 2016
```

---

## Copying production data from Heroku

Heroku app name: **`hampsteadwx-django`**. You need collaborator access and the Heroku CLI logged in (`heroku login`).

Add the git remote if you have not:

```bash
heroku git:remote -a hampsteadwx-django
```

### Option 1: `pg:pull` (simplest into local Postgres)

Creates or overwrites a **local** database from the Heroku Postgres add-on in one step:

```bash
# Local URL must use a database that exists (or that you are okay recreating)
export LOCAL_DATABASE_URL='postgres://hampsteadwx_dev@localhost:5432/hampsteadwx_local'

heroku pg:pull DATABASE_URL "$LOCAL_DATABASE_URL" -a hampsteadwx-django
```

Then point Django at that database:

```bash
export DATABASE_URL="$LOCAL_DATABASE_URL"
python manage.py migrate   # usually no-op if pull was complete
```

`pg:pull` uses `pg_dump` / `pg_restore` under the hood. Install PostgreSQL client tools locally if the command is missing.

### Option 2: Backup file (`pg:backups`)

Useful for archives or when you cannot pull directly.

```bash
# On-demand backup of the primary database
heroku pg:backups:capture -a hampsteadwx-django

# List backups
heroku pg:backups -a hampsteadwx-django

# Download latest (writes latest.dump in the current directory)
heroku pg:backups:download -a hampsteadwx-django

# Restore into local Postgres (custom format dump)
pg_restore --verbose --clean --no-acl --no-owner \
  -d hampsteadwx_local latest.dump
```

If `pg_restore` errors on `--clean` because objects do not exist, create an empty database first or drop/recreate `hampsteadwx_local`.

### Option 3: `pg:dump` to SQL

```bash
heroku pg:dump -a hampsteadwx-django -f production.sql
psql hampsteadwx_local < production.sql
```

### Inspect Heroku database config

```bash
heroku config:get DATABASE_URL -a hampsteadwx-django
heroku pg:info -a hampsteadwx-django
```

**Caution:** Production data may include real site content. Do not commit dumps (`*.dump`, `*.sql`) to git. Add them to `.gitignore` if you store them in the repo tree.

---

## Deploying to Heroku (reference)

This repo is set up for Heroku buildpack deployment:

- `Procfile` — Gunicorn WSGI server
- `runtime.txt` — Python version
- `pyproject.toml` — project metadata and dependencies (source of truth)
- `requirements.txt` — production export for Heroku (`uv export --no-dev --no-hashes -o requirements.txt`)

Typical config vars on the app:

- `SECRET_KEY`
- `DATABASE_URL` (set automatically when Postgres is attached)

```bash
git push heroku main
heroku run python manage.py migrate -a hampsteadwx-django
heroku logs --tail -a hampsteadwx-django
```

---

## Project layout (quick reference)

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, Ruff, ty, and pytest configuration |
| `boilerplate/settings.py` | Django settings; DB via `DATABASE_URL` |
| `boilerplate/settings_secret.py.template` | Copy to `settings_secret.py` for local `DEBUG` / hosts |
| `boilerplate/settings_secret.py` | Local overrides (gitignored) |
| `api/models.py` | Observations and summary models (Postgres arrays) |
| `api/utils.py` | Summary calculations |
| `api/management/commands/bulk_recalc.py` | Batch recalculation |
| `tests/conftest.py` | Shared pytest env defaults and helpers |
| `tests/fixtures/` | Sample observation CSV for tests |
| `tests/unit/` | Fast unit tests (mocked ORM/filesystem) |
| `tests/integration/` | PostgreSQL-backed integration tests |
| `static/csv/` | Climate normals CSV inputs |
| `templates/` | Summary and layout templates |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `django.db.utils.ProgrammingError` mentioning arrays | Database is not PostgreSQL (e.g. SQLite) |
| `DisallowedHost` | Enable `settings_secret.py` with `ALLOWED_HOSTS = ['*']` or add `127.0.0.1` |
| `SECRET_KEY` / `DATABASE_URL` errors | Exports missing; check `heroku config` for production values |
| `pg:pull` fails | Heroku CLI not logged in, missing local `pg_restore`, or Postgres not running |
| Empty site after fresh migrate | No data yet — run `pg:pull` or load observations via your usual ingestion path |
| `pytest` / integration: cannot connect to database | Postgres not running, bad `DATABASE_URL`, or test DB missing — create it (`createdb …`) and retry |
| Integration tests deselected unexpectedly | Default `addopts` is `-m "not integration"`; use `-m integration` or `-m "unit or integration"` |
