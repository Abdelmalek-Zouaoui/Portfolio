# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-user portfolio site built with FastAPI: a public page (profile, skills, projects) plus a password-protected `/admin` UI for editing all of that content and uploading images/resume to Cloudinary. Data lives in Turso (libSQL), accessed with raw SQL — no ORM.

## Commands

```powershell
# setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run locally (reads .env via python-dotenv)
uvicorn main:app --reload
```

Public page: http://127.0.0.1:8000/ — Admin: http://127.0.0.1:8000/admin

There is no test suite, linter, or build step configured in this repo.

Required env vars (app fails at startup/import without them): `ADMIN_PASSWORD`, `SESSION_SECRET`, `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`. Optional: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (uploads fail without these, rest of the app still works).

## Architecture

**Two route surfaces, one app.** [main.py](main.py) owns the public routes (`/`, `/projects/{id}`) and app setup (session middleware, static mount, Jinja2 templates, the `startup` hook that calls `database.create_tables()`). [admin.py](admin.py) is a separate `APIRouter` with prefix `/admin`, included into the same app, holding every authenticated route (login, dashboard, profile, skills CRUD, projects CRUD, project image management).

**Auth is a single hardcoded user, not a table.** [auth.py](auth.py) hashes `ADMIN_PASSWORD` once at import time and compares against it; there's no users table. Session state is just `{"authenticated": True}` in a signed cookie (`SessionMiddleware`). Every admin route protects itself individually by calling the `_guard(request)` helper at the top and returning its redirect — there is no dependency-based or middleware-level enforcement, so a new admin route that forgets to call `_guard` is unprotected.

**Data access has no model layer, just SQL wrappers.** [database.py](database.py) exposes `fetchall`/`fetchone`/`run` over a libsql-client HTTP connection, plus the full `DDL` table definitions and startup bootstrap (including seeding the single `profile` row). [models.py](models.py) is a flat set of async functions per entity — no classes, no ORM — that admin.py and main.py call directly. `update_profile`/`update_project` take `**fields` and build `SET` clauses dynamically from whatever kwargs are passed.

**Schema shape:**
- `profile` — singleton row (`id = 1`, seeded on startup), holds hero/about text and the resume PDF URL.
- `skills` — flat rows grouped by `category` at read time (`models.get_skills_grouped`), not a separate categories table.
- `projects` — core project fields; `project_meta` (key/value pairs, e.g. arbitrary spec rows) and `project_images` are child tables on `project_id` with `ON DELETE CASCADE`, but app code also deletes children explicitly before deleting a project (see `models.delete_project`) since libSQL cascade behavior isn't relied on alone.
- `project_images.is_main` marks the hero image for a project; `models.set_main_image` unsets all others first. The *first* uploaded image for a project is auto-marked main (`admin.py` `image_upload` checks `has_main` before each insert).

**Cloudinary is the only file store — nothing persists to local disk.** [storage.py](storage.py) has `upload_image` (resource_type `image`) and `upload_pdf` (resource_type `raw`, fixed `public_id="resume.pdf"` with `overwrite=True` so re-uploads replace the file in place rather than orphaning a new blob each time — raw resources don't get an automatic extension from Cloudinary, so the `.pdf` must be baked into the public_id or the served URL has no extension). Deleting a project or image also calls `storage.delete_file` to clean up the corresponding Cloudinary asset. Upload calls run via `run_in_threadpool` since the Cloudinary SDK is synchronous.

**Page data assembly is centralized.** `models.get_public_data()` and `models.get_project_full()` are the only two entry points the public routes use; both enrich raw project rows with `images`, `meta`, and a parsed `tags_list` (comma-separated `tags` column split into a list) rather than leaving that enrichment to templates.

**Local files not part of the running app:** `local.db` at the repo root is an unused leftover — the app only talks to Turso via `TURSO_DATABASE_URL`, there is no SQLite fallback path in `database.py` despite the README mentioning it as a possible future addition.

## Known rough edges (don't "fix" without asking — may be intentional/WIP)

- [auth.py:31](auth.py#L31) prints the plaintext password attempt and hash on every login check (`DEBUG AUTH: ...`) — this leaks the admin password into logs.
- `SessionMiddleware` in [main.py](main.py) is configured with `https_only=False`; the comment notes it should be `True` behind Render's HTTPS proxy.
