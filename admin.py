"""
admin.py — All /admin/* routes.

Protected by session cookie; any unauthenticated request redirects to /admin/login.
"""
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from typing import Annotated, Optional

import models
import storage
from auth import is_authenticated, verify_password, login_session, logout_session

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


# ── Auth guard helper ─────────────────────────────────────────────────────────

def _guard(request: Request) -> RedirectResponse | None:
    if not is_authenticated(request):
        return RedirectResponse("/admin/login", status_code=302)
    return None


# ── Login / Logout ────────────────────────────────────────────────────────────

@router.get("/login")
async def login_page(request: Request, error: str = ""):
    if is_authenticated(request):
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": error}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    password: Annotated[str, Form()],
):
    if verify_password(password):
        login_session(request)
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": "Incorrect password. Try again."},
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request):
    logout_session(request)
    return RedirectResponse("/admin/login", status_code=302)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/")
async def dashboard(request: Request):
    if (redir := _guard(request)):
        return redir
    projects = await models.get_all_projects()
    skills = await models.get_all_skills()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "project_count": len(projects),
            "skill_count": len(skills),
        },
    )


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile")
async def profile_page(request: Request, saved: str = ""):
    if (redir := _guard(request)):
        return redir
    profile = await models.get_profile()
    return templates.TemplateResponse(
        "admin/profile.html", {"request": request, "profile": profile, "saved": saved}
    )


@router.post("/profile")
async def profile_save(
    request: Request,
    name: Annotated[str, Form()] = "",
    eyebrow: Annotated[str, Form()] = "",
    hero_headline: Annotated[str, Form()] = "",
    hero_subtitle: Annotated[str, Form()] = "",
    about_text: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    github_url: Annotated[str, Form()] = "",
    linkedin_url: Annotated[str, Form()] = "",
    resume_file: Annotated[Optional[UploadFile], File()] = None,
):
    if (redir := _guard(request)):
        return redir

    profile = await models.get_profile()
    resume_url = profile.get("resume_file", "")

    # Upload new resume PDF to Cloudinary if provided
    if resume_file and resume_file.filename:
        file_bytes = await resume_file.read()
        if file_bytes:
            url, _pub_id = await run_in_threadpool(storage.upload_pdf, file_bytes)
            resume_url = url

    await models.update_profile(
        name=name,
        eyebrow=eyebrow,
        hero_headline=hero_headline,
        hero_subtitle=hero_subtitle,
        about_text=about_text,
        email=email,
        github_url=github_url,
        linkedin_url=linkedin_url,
        resume_file=resume_url,
    )
    return RedirectResponse("/admin/profile?saved=1", status_code=302)


# ── Skills ────────────────────────────────────────────────────────────────────

@router.get("/skills")
async def skills_page(request: Request, saved: str = ""):
    if (redir := _guard(request)):
        return redir
    skills = await models.get_all_skills()
    grouped = {}
    for s in skills:
        grouped.setdefault(s["category"], []).append(s)
    return templates.TemplateResponse(
        "admin/skills.html",
        {"request": request, "grouped": grouped, "skills": skills, "saved": saved},
    )


@router.post("/skills/add")
async def skill_add(
    request: Request,
    category: Annotated[str, Form()],
    label: Annotated[str, Form()],
    sort_order: Annotated[int, Form()] = 0,
):
    if (redir := _guard(request)):
        return redir
    await models.create_skill(category.strip(), label.strip(), sort_order)
    return RedirectResponse("/admin/skills?saved=1", status_code=302)


@router.post("/skills/{skill_id}/edit")
async def skill_edit(
    request: Request,
    skill_id: int,
    category: Annotated[str, Form()],
    label: Annotated[str, Form()],
    sort_order: Annotated[int, Form()] = 0,
):
    if (redir := _guard(request)):
        return redir
    await models.update_skill(skill_id, category.strip(), label.strip(), sort_order)
    return RedirectResponse("/admin/skills?saved=1", status_code=302)


@router.post("/skills/{skill_id}/delete")
async def skill_delete(request: Request, skill_id: int):
    if (redir := _guard(request)):
        return redir
    await models.delete_skill(skill_id)
    return RedirectResponse("/admin/skills?saved=1", status_code=302)


# ── Projects list ─────────────────────────────────────────────────────────────

@router.get("/projects")
async def projects_page(request: Request, saved: str = ""):
    if (redir := _guard(request)):
        return redir
    projects = await models.get_all_projects()
    return templates.TemplateResponse(
        "admin/projects.html",
        {"request": request, "projects": projects, "saved": saved},
    )


# ── Project create ────────────────────────────────────────────────────────────

@router.get("/projects/new")
async def project_new_page(request: Request):
    if (redir := _guard(request)):
        return redir
    return templates.TemplateResponse(
        "admin/project_edit.html",
        {"request": request, "project": None, "meta": [], "images": []},
    )


@router.post("/projects/new")
async def project_new_submit(
    request: Request,
    title: Annotated[str, Form()],
    index_label: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    link_url: Annotated[str, Form()] = "",
    link_label: Annotated[str, Form()] = "",
    status: Annotated[str, Form()] = "",
    sort_order: Annotated[int, Form()] = 0,
    meta_keys: Annotated[list[str], Form()] = [],
    meta_values: Annotated[list[str], Form()] = [],
):
    if (redir := _guard(request)):
        return redir
    project_id = await models.create_project(
        title=title,
        index_label=index_label,
        description=description,
        tags=tags,
        link_url=link_url,
        link_label=link_label,
        status=status,
        sort_order=sort_order,
    )
    meta_rows = [
        {"key": k, "value": v}
        for k, v in zip(meta_keys, meta_values)
        if k.strip()
    ]
    await models.replace_project_meta(project_id, meta_rows)
    return RedirectResponse(f"/admin/projects/{project_id}/edit?saved=1", status_code=302)


# ── Project edit ──────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/edit")
async def project_edit_page(request: Request, project_id: int, saved: str = ""):
    if (redir := _guard(request)):
        return redir
    project = await models.get_project(project_id)
    if not project:
        return RedirectResponse("/admin/projects", status_code=302)
    meta = await models.get_project_meta(project_id)
    images = await models.get_project_images(project_id)
    return templates.TemplateResponse(
        "admin/project_edit.html",
        {
            "request": request,
            "project": project,
            "meta": meta,
            "images": images,
            "saved": saved,
        },
    )


@router.post("/projects/{project_id}/edit")
async def project_edit_submit(
    request: Request,
    project_id: int,
    title: Annotated[str, Form()],
    index_label: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    link_url: Annotated[str, Form()] = "",
    link_label: Annotated[str, Form()] = "",
    status: Annotated[str, Form()] = "",
    sort_order: Annotated[int, Form()] = 0,
    meta_keys: Annotated[list[str], Form()] = [],
    meta_values: Annotated[list[str], Form()] = [],
):
    if (redir := _guard(request)):
        return redir
    await models.update_project(
        project_id,
        title=title,
        index_label=index_label,
        description=description,
        tags=tags,
        link_url=link_url,
        link_label=link_label,
        status=status,
        sort_order=sort_order,
    )
    meta_rows = [
        {"key": k, "value": v}
        for k, v in zip(meta_keys, meta_values)
        if k.strip()
    ]
    await models.replace_project_meta(project_id, meta_rows)
    return RedirectResponse(f"/admin/projects/{project_id}/edit?saved=1", status_code=302)


@router.post("/projects/{project_id}/delete")
async def project_delete(request: Request, project_id: int):
    if (redir := _guard(request)):
        return redir
    # Delete associated Cloudinary images first
    images = await models.get_project_images(project_id)
    for img in images:
        pub_id = img.get("cloudinary_public_id", "")
        if pub_id:
            await run_in_threadpool(storage.delete_file, pub_id)
    await models.delete_project(project_id)
    return RedirectResponse("/admin/projects?saved=1", status_code=302)


# ── Image management ──────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/images/upload")
async def image_upload(
    request: Request,
    project_id: int,
    images: list[UploadFile] = File(...),
    alt_text: Annotated[str, Form()] = "",
    sort_order: Annotated[int, Form()] = 0,
):
    if (redir := _guard(request)):
        return redir

    existing = await models.get_project_images(project_id)
    has_main = any(img.get("is_main") for img in existing)

    uploaded_count = 0
    for idx, img in enumerate(images):
        if not img.filename:
            continue
        file_bytes = await img.read()
        if not file_bytes:
            continue

        secure_url, public_id = await run_in_threadpool(storage.upload_image, file_bytes)

        # Set main image if project currently has no main image
        is_main = 1 if not has_main else 0
        if is_main:
            has_main = True

        img_alt = alt_text.strip()
        current_sort_order = sort_order + idx

        await models.add_project_image(
            project_id=project_id,
            image_path=secure_url,
            cloudinary_public_id=public_id,
            alt_text=img_alt,
            is_main=is_main,
            sort_order=current_sort_order,
        )
        uploaded_count += 1

    if uploaded_count == 0:
        return RedirectResponse(
            f"/admin/projects/{project_id}/edit?saved=error", status_code=302
        )

    return RedirectResponse(f"/admin/projects/{project_id}/edit?saved=1", status_code=302)


@router.post("/projects/{project_id}/images/{image_id}/delete")
async def image_delete(request: Request, project_id: int, image_id: int):
    if (redir := _guard(request)):
        return redir
    img = await models.get_image(image_id)
    if img:
        pub_id = img.get("cloudinary_public_id", "")
        if pub_id:
            await run_in_threadpool(storage.delete_file, pub_id)
        await models.delete_image(image_id)
    return RedirectResponse(f"/admin/projects/{project_id}/edit?saved=1", status_code=302)


@router.post("/projects/{project_id}/images/{image_id}/set-main")
async def image_set_main(request: Request, project_id: int, image_id: int):
    if (redir := _guard(request)):
        return redir
    await models.set_main_image(project_id, image_id)
    return RedirectResponse(f"/admin/projects/{project_id}/edit?saved=1", status_code=302)
