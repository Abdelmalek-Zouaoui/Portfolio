# Portfolio (FastAPI)

This is a small single-user portfolio admin app built with FastAPI. It provides:

- A public index page that renders profile, skills, and projects.
- A protected `/admin` UI for editing profile, skills, projects, and uploading files to Cloudinary.
- Data storage via libSQL (Turso) with simple SQL access helpers.

**Purpose of this README**

This file now includes a concise technical description and a debugging checklist you can send to an AI (or a developer) to help diagnose problems quickly.

**Tech Stack**

- Python 3.10+
- FastAPI (HTTP API + Jinja2 templates)
- Uvicorn (ASGI server)
- libsql-client (Turso / libSQL)
- Cloudinary (image / PDF uploads)
- passlib + bcrypt (password hashing)
- python-multipart (form/file parsing)

**Key files**

- [main.py](main.py) — app entrypoint, middleware, static mounting, and public index route.
- [database.py](database.py) — libsql client factory, SQL helpers, and table DDL/bootstrap.
- [models.py](models.py) — async data-access functions used by routes.
- [admin.py](admin.py) — all `/admin/*` routes and form handling.
- [auth.py](auth.py) — session-based single-user auth using `ADMIN_PASSWORD`.
- [storage.py](storage.py) — Cloudinary upload/delete helpers.
- [render.yaml](render.yaml) — Render deployment config.
- `templates/` and `static/` — Jinja2 templates and assets for public and admin UIs.

**Environment variables (summary)**

- `ADMIN_PASSWORD` — required. Single-user admin password (hashed at import time).
- `SESSION_SECRET` — required for session cookie signing.
- `TURSO_DATABASE_URL` / `TURSO_AUTH_TOKEN` — required for Turso/libSQL in production (if unset, startup will fail).
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` — optional for uploads (storage functions call these).
- `PORT` — server port (Render sets this).

See [.env.example](.env.example) for a minimal template.

**How to run locally**

1. Copy `.env.example` → `.env` and fill values (at minimum `ADMIN_PASSWORD` and `SESSION_SECRET`).

2. Create and activate a virtual environment and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Start the app:

```powershell
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ for the public page and http://127.0.0.1:8000/admin for the admin UI.

**Debugging checklist for AI / developer**

When sending this repo to an AI or another developer to fix a problem, include the following information to speed up diagnosis:

- **Environment:** OS, Python version (`python --version`), whether running inside a venv, and `pip freeze` output.
- **Exact steps to reproduce:** HTTP method, URL path, form fields or JSON body, and any headers (e.g., cookies, auth).
- **Commands run:** the exact commands you used to start the app and any build steps.
- **Full error output / traceback:** copy-paste the full exception and stack trace from the server logs (not just the top line).
- **Relevant log lines:** app startup logs, requests around the failure time, and any printed debug statements (e.g., `DEBUG AUTH` in `auth.py`).
- **Environment variables:** list which env vars you set and which you left unset (do NOT share secrets; redact values).
- **Database state:** run sample queries and include outputs, for example:

```sql
SELECT * FROM profile;
SELECT * FROM projects LIMIT 5;
```

- **Request sample (curl):** provide a minimal `curl` example that reproduces the issue, for example:

```bash
curl -X POST \
	-F "password=yourpass" \
	http://127.0.0.1:8000/admin/login
```

- **Screenshots or HTML snippets** when UI rendering is the problem.
- **Expected vs actual behavior**: short bullets describing what you expect and what happens instead.

**Common gotchas to check first**

- If the app errors on startup with a KeyError: set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` or implement a local fallback.
- The admin password is required at import time by `auth.py`; if you see an import-time RuntimeError, ensure `ADMIN_PASSWORD` is set.
- File uploads use Cloudinary; missing `CLOUDINARY_*` will cause upload API errors.

If you want, I can add a local SQLite fallback to `database.py` so the app starts without Turso — say the word and I'll implement it.

**What I changed in this repo**

- Added an initial `requirements.txt`.
- Added `.env.example` to document environment variables.
- Expanded this `README.md` with technical details and a debugging checklist.

**Next suggestions (pick one)**

- Add a SQLite local fallback in `database.py` so the app runs without Turso.
- Add minimal automated tests and a GitHub Actions workflow.
- Run the app here and reproduce an error (provide the failing request) so I can triage it.

