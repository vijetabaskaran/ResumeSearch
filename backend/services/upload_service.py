import os
import urllib.parse
import uuid
from dataclasses import dataclass

import fitz
import requests
from fastapi import UploadFile


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
UPLOAD_BASE_URL = "http://127.0.0.1:8000/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@dataclass
class SavedUpload:
    filename: str
    filepath: str
    url: str
    extension: str
    contents: bytes
    text: str


def _extension(filename):
    return os.path.splitext(filename or "")[1].lower()


def _safe_upload_name(original_filename, prefix=""):
    name = os.path.basename(original_filename or "upload")
    return f"{prefix}{uuid.uuid4()}_{name}"


def _decode_text(contents):
    try:
        return contents.decode("utf-8").strip()
    except UnicodeDecodeError:
        return contents.decode("latin-1").strip()


def extract_text(filepath, extension, contents):
    if extension == ".pdf":
        doc = fitz.open(filepath)
        try:
            return "".join(page.get_text() for page in doc).strip()
        finally:
            doc.close()

    if extension == ".txt":
        return _decode_text(contents)

    return ""


def _save_bytes(contents, original_filename, prefix=""):
    safe_filename = _safe_upload_name(original_filename, prefix)
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    with open(filepath, "wb") as file_handle:
        file_handle.write(contents)
    return safe_filename, filepath


async def handle_upload(
    file: UploadFile = None,
    source_url: str = None,
    allowed_extensions=(".pdf",),
    prefix="",
    default_url_filename="upload.pdf"
):
    """Validate, save, and extract text from either an uploaded file or URL."""
    if not file and not source_url:
        raise ValueError("Please provide either a file or a URL.")

    if file:
        original_filename = file.filename or default_url_filename
        extension = _extension(original_filename)
        if extension not in allowed_extensions:
            allowed = ", ".join(allowed_extensions)
            raise ValueError(f"Only {allowed} files are supported.")

        contents = await file.read()
        safe_filename, filepath = _save_bytes(contents, original_filename, prefix)
    else:
        source_url = source_url.strip()
        if not (source_url.startswith("http://") or source_url.startswith("https://")):
            raise ValueError("Invalid URL. Must start with http:// or https://")

        response = requests.get(source_url, timeout=20)
        if response.status_code != 200:
            raise ValueError(f"Failed to download file from URL (status code: {response.status_code})")

        contents = response.content
        parsed_url = urllib.parse.urlparse(source_url)
        original_filename = os.path.basename(parsed_url.path) or default_url_filename
        extension = _extension(original_filename)

        if extension not in allowed_extensions:
            original_filename = default_url_filename
            extension = _extension(original_filename)

        safe_filename, filepath = _save_bytes(contents, original_filename, prefix)

    text = extract_text(filepath, extension, contents)
    if not text:
        raise ValueError("Could not extract any text content from the uploaded file.")

    return SavedUpload(
        filename=safe_filename,
        filepath=filepath,
        url=f"{UPLOAD_BASE_URL}/{safe_filename}",
        extension=extension,
        contents=contents,
        text=text
    )
