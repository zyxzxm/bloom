"""Small Supabase Storage adapter; local mode remains the default for development."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "bloom-assets")


def enabled() -> bool:
    if bool(SUPABASE_URL) != bool(SUPABASE_SERVICE_ROLE_KEY):
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY juntos")
    return bool(SUPABASE_URL)


def _url(key: str) -> str:
    bucket = quote(BUCKET, safe="")
    object_key = quote(key.lstrip("/"), safe="/")
    return f"{SUPABASE_URL}/storage/v1/object/{bucket}/{object_key}"


def _headers(content_type: str | None = None) -> dict[str, str]:
    key = SUPABASE_SERVICE_ROLE_KEY
    headers = {
        "apikey": key,
    }
    # New Supabase API keys are not JWTs and must not be sent as Bearer tokens.
    # Legacy service_role keys are JWTs and continue to work with both headers.
    if not key.startswith(("sb_secret_", "sb_publishable_")):
        headers["Authorization"] = f"Bearer {key}"
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def upload_file(path: Path, key: str, content_type: str) -> None:
    size = path.stat().st_size
    headers = _headers(content_type)
    headers["x-upsert"] = "true"
    headers["Content-Length"] = str(size)

    def chunks():
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                yield chunk

    with httpx.Client(timeout=httpx.Timeout(300.0, connect=20.0)) as client:
        response = client.post(_url(key), headers=headers, content=chunks())
        response.raise_for_status()


def download_file(key: str, destination: Path) -> None:
    headers = _headers()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=httpx.Timeout(300.0, connect=20.0)) as client:
        with client.stream("GET", _url(key), headers=headers) as response:
            if response.status_code == 404:
                raise FileNotFoundError(key)
            response.raise_for_status()
            with destination.open("wb") as stream:
                for chunk in response.iter_bytes(1024 * 1024):
                    stream.write(chunk)


def delete_object(key: str) -> None:
    headers = _headers("application/json")
    with httpx.Client(timeout=30.0) as client:
        response = client.request(
            "DELETE",
            f"{SUPABASE_URL}/storage/v1/object/{quote(BUCKET, safe='')}",
            headers=headers,
            json={"prefixes": [key.lstrip("/")]},
        )
        if response.status_code not in (200, 204, 404):
            response.raise_for_status()
