"""
storage.py — Cloudinary upload / delete helpers.

All credentials are read from environment variables.
Files are streamed as bytes — never written to local disk.
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api


def _configure():
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_image(file_bytes: bytes, folder: str = "portfolio") -> tuple[str, str]:
    """
    Upload image bytes to Cloudinary.
    Returns (secure_url, public_id).
    """
    _configure()
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="image",
    )
    return result["secure_url"], result["public_id"]


def upload_pdf(file_bytes: bytes, folder: str = "portfolio/resumes") -> tuple[str, str]:
    """
    Upload a PDF (or any raw file) to Cloudinary.
    Returns (secure_url, public_id).
    """
    _configure()
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="raw",
    )
    return result["secure_url"], result["public_id"]


def delete_file(public_id: str, resource_type: str = "image") -> None:
    """Delete a file from Cloudinary by its public_id."""
    _configure()
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception:
        pass  # Log in production; don't crash if already deleted
