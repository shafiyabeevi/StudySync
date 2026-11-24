from urllib.parse import quote

import httpx

from app.core.config import get_settings


class SupabaseStorageError(RuntimeError):
    pass


def _storage_url(bucket: str, path: str) -> str:
    settings = get_settings()
    return (
        f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/"
        f"{quote(bucket, safe='')}/{quote(path, safe='/')}"
    )


def _headers(access_token: str) -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.SUPABASE_ANON_KEY.strip(),
        "Authorization": f"Bearer {access_token}",
    }


def _raise_storage_error(response: httpx.Response) -> None:
    if response.is_error:
        raise SupabaseStorageError(
            f"Supabase Storage returned HTTP {response.status_code}."
        )


async def upload_storage_object(
    access_token: str,
    bucket: str,
    path: str,
    content: bytes,
    content_type: str,
) -> None:
    headers = {
        **_headers(access_token),
        "Content-Type": content_type,
        "x-upsert": "false",
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                _storage_url(bucket, path), headers=headers, content=content
            )
    except httpx.RequestError as exc:
        raise SupabaseStorageError("Could not reach Supabase Storage.") from exc
    _raise_storage_error(response)


async def download_storage_object(
    access_token: str,
    bucket: str,
    path: str,
) -> bytes:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                _storage_url(bucket, path), headers=_headers(access_token)
            )
    except httpx.RequestError as exc:
        raise SupabaseStorageError("Could not reach Supabase Storage.") from exc
    _raise_storage_error(response)
    return response.content


async def delete_storage_object(
    access_token: str,
    bucket: str,
    path: str,
) -> None:
    settings = get_settings()
    url = (
        f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/"
        f"{quote(bucket, safe='')}"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                url,
                headers={**_headers(access_token), "Content-Type": "application/json"},
                json={"prefixes": [path]},
            )
    except httpx.RequestError as exc:
        raise SupabaseStorageError("Could not reach Supabase Storage.") from exc
    _raise_storage_error(response)
