"""
auth.py — Session-based single-user admin authentication.

Uses Starlette SessionMiddleware (signed cookie via itsdangerous).
The admin password is read from ADMIN_PASSWORD env var and hashed
with passlib/bcrypt at module load time.
"""
import os
from functools import lru_cache

from fastapi import Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@lru_cache(maxsize=1)
def _get_password_hash() -> str:
    """Hash ADMIN_PASSWORD once at import time (cached)."""
    raw = os.environ.get("ADMIN_PASSWORD", "")
    if not raw:
        raise RuntimeError("ADMIN_PASSWORD environment variable is not set.")
    return pwd_context.hash(raw)


def verify_password(plain: str) -> bool:
    try:
        h = _get_password_hash()
        v = pwd_context.verify(plain, h)
        print(f"DEBUG AUTH: plain={plain!r}, env_pass={os.environ.get('ADMIN_PASSWORD')!r}, hash={h!r}, result={v}")
        return v
    except Exception as e:
        print(f"DEBUG AUTH ERROR: {e}")
        return False


def is_authenticated(request: Request) -> bool:
    return request.session.get("authenticated") is True


def login_session(request: Request) -> None:
    request.session["authenticated"] = True


def logout_session(request: Request) -> None:
    request.session.clear()


def require_auth(request: Request) -> None:
    """
    Dependency — raise a redirect to /admin/login if not authenticated.
    Use as:  _: None = Depends(require_auth)
    """
    if not is_authenticated(request):
        # FastAPI doesn't support raising redirects from Depends directly,
        # so we raise an HTTPException and catch it in admin.py.
        from fastapi import HTTPException
        raise HTTPException(status_code=307, detail="/admin/login")
