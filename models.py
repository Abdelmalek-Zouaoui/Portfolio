"""
models.py — All data-access functions.

Pure async functions wrapping raw SQL queries via database.py helpers.
No ORM — keeps things straightforward with Turso/libSQL.
"""
from database import fetchall, fetchone, run


# ─── Profile ────────────────────────────────────────────────────────────────

async def get_profile() -> dict:
    row = await fetchone("SELECT * FROM profile WHERE id = 1")
    return row or {}


async def update_profile(**fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values())
    await run(f"UPDATE profile SET {set_clause} WHERE id = 1", values)


# ─── Skills ─────────────────────────────────────────────────────────────────

async def get_all_skills() -> list[dict]:
    return await fetchall(
        "SELECT * FROM skills ORDER BY category, sort_order, label"
    )


async def get_skills_grouped() -> dict[str, list[dict]]:
    """Return {category: [skill, …]} ordered by sort_order."""
    rows = await get_all_skills()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
    return grouped


async def get_skill(skill_id: int) -> dict | None:
    return await fetchone("SELECT * FROM skills WHERE id = ?", [skill_id])


async def create_skill(category: str, label: str, sort_order: int = 0) -> None:
    await run(
        "INSERT INTO skills (category, label, sort_order) VALUES (?, ?, ?)",
        [category, label, sort_order],
    )


async def update_skill(skill_id: int, category: str, label: str, sort_order: int) -> None:
    await run(
        "UPDATE skills SET category = ?, label = ?, sort_order = ? WHERE id = ?",
        [category, label, sort_order, skill_id],
    )


async def delete_skill(skill_id: int) -> None:
    await run("DELETE FROM skills WHERE id = ?", [skill_id])


# ─── Projects ───────────────────────────────────────────────────────────────

async def get_all_projects() -> list[dict]:
    return await fetchall("SELECT * FROM projects ORDER BY sort_order, id")


async def get_project(project_id: int) -> dict | None:
    return await fetchone("SELECT * FROM projects WHERE id = ?", [project_id])


async def create_project(
    title: str,
    index_label: str = "",
    description: str = "",
    tags: str = "",
    link_url: str = "",
    link_label: str = "",
    status: str = "",
    sort_order: int = 0,
) -> int:
    """Insert project, return new id."""
    await run(
        "INSERT INTO projects (title, index_label, description, tags, "
        "link_url, link_label, status, sort_order) VALUES (?,?,?,?,?,?,?,?)",
        [title, index_label, description, tags, link_url, link_label, status, sort_order],
    )
    row = await fetchone("SELECT last_insert_rowid() AS id")
    return int(row["id"]) if row else 0


async def update_project(project_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [project_id]
    await run(f"UPDATE projects SET {set_clause} WHERE id = ?", values)


async def delete_project(project_id: int) -> None:
    await run("DELETE FROM project_meta WHERE project_id = ?", [project_id])
    await run("DELETE FROM project_images WHERE project_id = ?", [project_id])
    await run("DELETE FROM projects WHERE id = ?", [project_id])


# ─── Project Meta ────────────────────────────────────────────────────────────

async def get_project_meta(project_id: int) -> list[dict]:
    return await fetchall(
        "SELECT * FROM project_meta WHERE project_id = ? ORDER BY sort_order, id",
        [project_id],
    )


async def replace_project_meta(project_id: int, rows: list[dict]) -> None:
    """Delete all meta for project, then insert fresh rows."""
    await run("DELETE FROM project_meta WHERE project_id = ?", [project_id])
    for i, row in enumerate(rows):
        key = row.get("key", "").strip()
        value = row.get("value", "").strip()
        if key:
            await run(
                "INSERT INTO project_meta (project_id, key, value, sort_order) VALUES (?,?,?,?)",
                [project_id, key, value, i],
            )


# ─── Project Images ──────────────────────────────────────────────────────────

async def get_project_images(project_id: int) -> list[dict]:
    return await fetchall(
        "SELECT * FROM project_images WHERE project_id = ? ORDER BY is_main DESC, sort_order, id",
        [project_id],
    )


async def add_project_image(
    project_id: int,
    image_path: str,
    cloudinary_public_id: str,
    alt_text: str = "",
    is_main: int = 0,
    sort_order: int = 0,
) -> int:
    await run(
        "INSERT INTO project_images (project_id, image_path, cloudinary_public_id, "
        "alt_text, is_main, sort_order) VALUES (?,?,?,?,?,?)",
        [project_id, image_path, cloudinary_public_id, alt_text, is_main, sort_order],
    )
    row = await fetchone("SELECT last_insert_rowid() AS id")
    return int(row["id"]) if row else 0


async def get_image(image_id: int) -> dict | None:
    return await fetchone("SELECT * FROM project_images WHERE id = ?", [image_id])


async def delete_image(image_id: int) -> None:
    await run("DELETE FROM project_images WHERE id = ?", [image_id])


async def set_main_image(project_id: int, image_id: int) -> None:
    await run(
        "UPDATE project_images SET is_main = 0 WHERE project_id = ?", [project_id]
    )
    await run(
        "UPDATE project_images SET is_main = 1 WHERE id = ?", [image_id]
    )


async def update_image_alt(image_id: int, alt_text: str) -> None:
    await run("UPDATE project_images SET alt_text = ? WHERE id = ?", [alt_text, image_id])


# ─── Public page assembly ────────────────────────────────────────────────────

async def get_public_data() -> dict:
    """Fetch everything needed for the public index page in one place."""
    profile = await get_profile()
    skills_grouped = await get_skills_grouped()
    projects = await get_all_projects()

    enriched = []
    for p in projects:
        images = await get_project_images(p["id"])
        meta = await get_project_meta(p["id"])
        tags = [t.strip() for t in (p.get("tags") or "").split(",") if t.strip()]
        enriched.append({**p, "images": images, "meta": meta, "tags_list": tags})

    return {
        "profile": profile,
        "skills_grouped": skills_grouped,
        "projects": enriched,
    }
