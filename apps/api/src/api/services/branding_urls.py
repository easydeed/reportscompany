"""Branding image URLs may only point at our own storage (LR-007, Jerry's option 1).

A branding image (logo, footer logo, email logos, headshot / rep photo) is
fetched by the report renderers and shown to every recipient, so it must be
an image we checked and stored: an upload, or a pasted link imported through
POST /v1/upload/branding/{asset_type}/import. A save is accepted when each
image field is:

  * not sent, or empty (cleared);
  * a value already stored on the same record, in any image field. Existing
    saved values stay exactly as they are (Jerry: PCT's two SVG logos keep
    rendering), and a form may copy the header logo into the email logo; or
  * one of OUR storage URLs that an AUTHORIZED account stored (Codex #330 P2).
    Upload and import write `branding/{account_id}/{asset}_{ts}_{id}.{ext}`
    under the uploading account, so the caller names the accounts whose
    uploads this record may use (`owners`), and the object must be one the
    current pipeline writes: a single file name with a raster extension. A
    known URL from another account, or an old SVG not on this record, is
    refused.

Anything else is refused with 400 before anything is written.
"""
import re
from typing import Iterable, Mapping, Optional

from fastapi import HTTPException

from . import upload

LINK_REFUSED = ("{field}: images must be uploaded, or pasted with 'Or paste an image URL', which "
                "imports a checked copy. A link to another site can't be saved directly.")
NOT_YOURS = ("{field}: that image was uploaded by a different account. Upload it again here, or "
             "paste its link with 'Or paste an image URL'.")

# What upload.store_branding_image writes after the account prefix (the
# extensions upload.IMAGE_TYPES allows). No slash, no dot-segments, no escapes.
STORED_NAME = re.compile(r"[A-Za-z0-9_-]+\.(?:png|jpe?g|webp|gif)")
PLACEHOLDER = "https://via.placeholder.com/"


def _bases() -> list[tuple[str, bool]]:
    """(storage base ending in 'branding/', whether a query string is expected)."""
    bases = []
    if upload.R2_PUBLIC_URL:
        bases.append((f"{upload.R2_PUBLIC_URL.rstrip('/')}/branding/", False))
    if upload.R2_ENDPOINT:
        # Presigned URLs, used only when no public base is configured.
        bases.append((f"{upload.R2_ENDPOINT.rstrip('/')}/{upload.R2_BUCKET_NAME}/branding/", True))
    return bases


def storage_account(url: str) -> Optional[str]:
    """The account whose upload `url` is, if it is a well-formed object in our storage."""
    if not url or any(c in url for c in ("\\", "\n", "\r", "#")):
        return None
    for base, signed in _bases():
        if not url.startswith(base):
            continue
        rest = url[len(base):]
        path, _, query = rest.partition("?")
        if query and not signed:
            return None
        account, sep, name = path.partition("/")
        if sep and account and re.fullmatch(r"[A-Za-z0-9-]+", account) and STORED_NAME.fullmatch(name):
            return account
    return None


def is_own_storage_url(url: str, owners: Iterable[str]) -> bool:
    if url and url.startswith(PLACEHOLDER) and not upload.get_r2_client():
        return True     # local development without R2: the upload route returns this placeholder
    account = storage_account(url)
    return account is not None and account.lower() in {str(o).lower() for o in owners if o}


def check_image_urls(changes: Mapping[str, Optional[str]], existing: Iterable[Optional[str]] = (), *,
                     owners: Iterable[str]) -> None:
    """Raise 400 if any proposed image URL is neither already stored nor an authorized upload."""
    stored = {v for v in existing if v}
    owners = [o for o in owners if o]
    for field, value in changes.items():
        if value is None or value == "":
            continue
        if value in stored or is_own_storage_url(value, owners):
            continue
        if storage_account(value) is not None:
            raise HTTPException(status_code=400, detail=NOT_YOURS.format(field=field))
        raise HTTPException(status_code=400, detail=LINK_REFUSED.format(field=field))
