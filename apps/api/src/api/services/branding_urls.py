"""Branding image URLs may only point at our own storage (LR-007, Jerry's option 1).

A branding image (logo, footer logo, email logos, headshot / rep photo) is
fetched by the report renderers and shown to every recipient, so it must be
an image we checked and stored: an upload, or a pasted link imported through
POST /v1/upload/branding/{asset_type}/import. A save is accepted when each
image field is:

  * not sent, or empty (cleared);
  * one of OUR storage URLs (what upload and import return); or
  * a value already stored on the same record, in any image field. Existing
    saved values stay exactly as they are (Jerry: PCT's two SVG logos keep
    rendering), and a form may copy the header logo into the email logo.

Anything else is refused with 400 before anything is written.
"""
from typing import Iterable, Mapping, Optional

from fastapi import HTTPException

from . import upload

LINK_REFUSED = ("{field}: images must be uploaded, or pasted with 'Or paste an image URL', which "
                "imports a checked copy. A link to another site can't be saved directly.")


def own_storage_prefixes() -> list[str]:
    prefixes = []
    if upload.R2_PUBLIC_URL:
        prefixes.append(f"{upload.R2_PUBLIC_URL.rstrip('/')}/branding/")
    if upload.R2_ENDPOINT:
        # Presigned URLs, used only when no public base is configured.
        prefixes.append(f"{upload.R2_ENDPOINT.rstrip('/')}/{upload.R2_BUCKET_NAME}/branding/")
    if not upload.get_r2_client():
        # Local development without R2: the upload route returns this placeholder.
        prefixes.append("https://via.placeholder.com/")
    return prefixes


def is_own_storage_url(url: str) -> bool:
    if not url or any(c in url for c in ("\\", "\n", "\r")) or "/../" in url:
        return False
    return any(url.startswith(p) for p in own_storage_prefixes())


def check_image_urls(changes: Mapping[str, Optional[str]], existing: Iterable[Optional[str]] = ()) -> None:
    """Raise 400 if any proposed image URL is neither ours nor already stored."""
    stored = {v for v in existing if v}
    for field, value in changes.items():
        if value is None or value == "":
            continue
        if value in stored or is_own_storage_url(value):
            continue
        raise HTTPException(status_code=400, detail=LINK_REFUSED.format(field=field))
