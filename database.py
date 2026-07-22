"""
database.py — Turso (libSQL) connection and table bootstrap.

Uses the libsql-client HTTP-based Python client so it works on any host
(including Render) without compiling native binaries.

Environment variables required:
  TURSO_DATABASE_URL  — e.g. libsql://mydb.turso.io
  TURSO_AUTH_TOKEN    — Turso auth token
"""
import os
import asyncio
import libsql_client

# ---------------------------------------------------------------------------
# Connection factory — one shared client per process
# ---------------------------------------------------------------------------
_client: libsql_client.Client | None = None


def get_client() -> libsql_client.Client:
    global _client
    if _client is None:
        url = os.environ["TURSO_DATABASE_URL"]
        token = os.environ["TURSO_AUTH_TOKEN"]
        _client = libsql_client.create_client(url=url, auth_token=token)
    return _client


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

async def execute(sql: str, args: list | tuple = ()) -> libsql_client.ResultSet:
    """Run a single statement, return its ResultSet."""
    client = get_client()
    return await client.execute(libsql_client.Statement(sql, list(args)))


async def fetchall(sql: str, args: list | tuple = ()) -> list[dict]:
    """Run a SELECT, return list of row-dicts."""
    rs = await execute(sql, args)
    cols = rs.columns
    return [dict(zip(cols, row)) for row in rs.rows]


async def fetchone(sql: str, args: list | tuple = ()) -> dict | None:
    """Run a SELECT, return first row-dict or None."""
    rows = await fetchall(sql, args)
    return rows[0] if rows else None


async def run(sql: str, args: list | tuple = ()) -> None:
    """Run a write statement (INSERT / UPDATE / DELETE)."""
    await execute(sql, args)


# ---------------------------------------------------------------------------
# Table bootstrap — called once at app startup
# ---------------------------------------------------------------------------

DDL = [
    # Profile — always exactly one row (id = 1)
    """
    CREATE TABLE IF NOT EXISTS profile (
        id            INTEGER PRIMARY KEY DEFAULT 1,
        name          TEXT    DEFAULT '',
        eyebrow       TEXT    DEFAULT '',
        hero_headline TEXT    DEFAULT '',
        hero_subtitle TEXT    DEFAULT '',
        about_text    TEXT    DEFAULT '',
        email         TEXT    DEFAULT '',
        github_url    TEXT    DEFAULT '',
        linkedin_url  TEXT    DEFAULT '',
        resume_file   TEXT    DEFAULT ''
    )
    """,
    # Skills
    """
    CREATE TABLE IF NOT EXISTS skills (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        category   TEXT    NOT NULL,
        label      TEXT    NOT NULL,
        sort_order INTEGER DEFAULT 0
    )
    """,
    # Projects
    """
    CREATE TABLE IF NOT EXISTS projects (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT    NOT NULL,
        index_label TEXT    DEFAULT '',
        description TEXT    DEFAULT '',
        tags        TEXT    DEFAULT '',
        link_url    TEXT    DEFAULT '',
        link_label  TEXT    DEFAULT '',
        status      TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0
    )
    """,
    # Project meta key-value rows
    """
    CREATE TABLE IF NOT EXISTS project_meta (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        key        TEXT    NOT NULL,
        value      TEXT    DEFAULT '',
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """,
    # Project images (Cloudinary URLs, never local paths)
    """
    CREATE TABLE IF NOT EXISTS project_images (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id          INTEGER NOT NULL,
        image_path          TEXT    NOT NULL,
        cloudinary_public_id TEXT   DEFAULT '',
        alt_text            TEXT    DEFAULT '',
        is_main             INTEGER DEFAULT 0,
        sort_order          INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """,
]


async def create_tables() -> None:
    """Create all tables (if not exists) and seed the profile singleton."""
    client = get_client()
    stmts = [libsql_client.Statement(ddl.strip()) for ddl in DDL]
    await client.batch(stmts)

    # Ensure profile row exists
    existing = await fetchone("SELECT id FROM profile WHERE id = 1")
    if not existing:
        await run(
            "INSERT INTO profile (id, name, eyebrow, hero_headline, hero_subtitle, "
            "about_text, email, github_url, linkedin_url, resume_file) "
            "VALUES (1, '', '', '', '', '', '', '', '', '')"
        )
