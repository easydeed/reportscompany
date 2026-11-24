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
  * one of OUR storage objects that the CHECKED pipeline wrote, for an
    AUTHORIZED account (Codex #330 rounds 1 and 2). Upload and import now write
    `branding/{account_id}/checked/{logo|headshot}_{14-digit time}_{8 hex}.{ext}`,
    and only that exact shape is admissible as a new value:
      - the account must be one the route names in `owners`, so a known URL
        from another account is refused;
      - the `checked/` segment is proof of validation. Before #312 the
        uploader trusted the declared type and kept the file name, so SVG
        bytes uploaded as "logo.png" sit at `branding/{account}/logo_….png`.
        An extension proves nothing; that old layout can never contain the
        `checked/` segment (its asset type was only ever "logo" or
        "headshot"), so no pre-#330 object is admissible as a NEW value.
        Those objects stay where already saved, as decided.

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

# Exactly what upload.store_branding_image writes after `branding/{account}/`.
CHECKED_DIR = "checked"
STORED_NAME = re.compile(r"(?:logo|headshot)_\d{14}_[0-9a-f]{8}\.(?:png|jpe?g|webp|gif)")
LEGACY_UNCHECKED = ("{field}: that image was stored before uploads were checked, so it can't be newly "
                    "selected. Upload it again, or paste its link with 'Or paste an image URL'.")
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


def storage_object(url: str) -> Optional[tuple[str, bool]]:
    """(account, written by the checked pipeline) for a URL inside our branding storage, else None."""
    if not url or any(c in url for c in ("\\", "\n", "\r", "#")):
        return None
    for base, signed in _bases():
        if not url.startswith(base):
            continue
        path, _, query = url[len(base):].partition("?")
        account, sep, rest = path.partition("/")
        if not (sep and account and re.fullmatch(r"[A-Za-z0-9-]+", account)):
            return None
        directory, sep, name = rest.partition("/")
        checked = (bool(sep) and directory == CHECKED_DIR and STORED_NAME.fullmatch(name) is not None
                   and (signed or not query))
        return account, checked
    return None


def is_own_storage_url(url: str, owners: Iterable[str]) -> bool:
    """A checked-pipeline object stored for one of `owners`."""
    if url and url.startswith(PLACEHOLDER) and not upload.get_r2_client():
        return True     # local development without R2: the upload route returns this placeholder
    obj = storage_object(url)
    return obj is not None and obj[1] and obj[0].lower() in {str(o).lower() for o in owners if o}


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
        obj = storage_object(value)
        if obj is not None and obj[0].lower() not in {str(o).lower() for o in owners}:
            raise HTTPException(status_code=400, detail=NOT_YOURS.format(field=field))
        if obj is not None:
            raise HTTPException(status_code=400, detail=LEGACY_UNCHECKED.format(field=field))
        raise HTTPException(status_code=400, detail=LINK_REFUSED.format(field=field))
