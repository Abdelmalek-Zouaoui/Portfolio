"""
main.py — FastAPI app entry point.

Registers middleware, static files, routers, startup hook, and the public index route.
Nothing in this app writes to the local filesystem for persisted data.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env when running locally

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse
from fastapi import HTTPException

import database
import models
from admin import router as admin_router

app = FastAPI(title="Portfolio", docs_url=None, redoc_url=None)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-secret-change-me"),
    session_cookie="portfolio_session",
    same_site="lax",
    https_only=False,  # Set True if behind HTTPS proxy on Render
    max_age=60 * 60 * 24 * 7,  # 7 days
)

# ── Static files & templates ──────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(admin_router)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await database.create_tables()


# ── Public routes ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = await models.get_public_data()
    return templates.TemplateResponse("index.html", {"request": request, **data})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int):
    project = await models.get_project_full(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    profile = await models.get_profile()
    return templates.TemplateResponse(
        "project_detail.html",
        {"request": request, "project": project, "profile": profile},
    )
