"""
File upload routes for branding assets.

Pass B1.2: Upload API Endpoint
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from pydantic import BaseModel

from ..services.upload import (upload_branding_asset, delete_branding_asset, prepare_image,
                               store_branding_image, MAX_FILE_BYTES)
from ..services import safe_fetch
from .reports import require_account_id

router = APIRouter(prefix="/v1/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Response model for successful upload."""
    url: str
    filename: str
    size_bytes: int


class DeleteResponse(BaseModel):
    """Response model for delete operation."""
    ok: bool
    message: str


@router.post("/branding/{asset_type}", response_model=UploadResponse)
async def upload_branding_file(
    asset_type: str,
    request: Request,
    file: UploadFile = File(...),
    account_id: str = Depends(require_account_id)
):
    """
    Upload a branding asset (logo or headshot).
    
    - **asset_type**: "logo" or "headshot"
    - **file**: Image file (PNG, JPEG, WebP, GIF; max 5MB)
    
    Returns the public URL of the uploaded file.
    
    The uploaded file will be stored at:
    `branding/{account_id}/{asset_type}_{timestamp}_{unique_id}.{ext}`
    """
    if asset_type not in ("logo", "headshot"):
        raise HTTPException(
            status_code=400, 
            detail="asset_type must be 'logo' or 'headshot'"
        )
    
    result = await upload_branding_asset(file, account_id, asset_type)
    
    return UploadResponse(
        url=result["url"],
        filename=result["filename"],
        size_bytes=result["size_bytes"]
    )


class ImportRequest(BaseModel):
    url: str


@router.post("/branding/{asset_type}/import", response_model=UploadResponse)
def import_branding_image(
    asset_type: str,
    body: ImportRequest,
    request: Request,
    account_id: str = Depends(require_account_id),
):
    """Copy an image from a pasted link into our storage (LR-007, Jerry's option 1).

    The link is fetched by the guarded fetcher (public https hosts only, every
    redirect re-checked, size capped), then checked and re-encoded exactly like
    an upload. What is stored, and returned, is OUR copy: branding saves accept
    only our storage URLs, so a pasted link never reaches a report directly.
    """
    if asset_type not in ("logo", "headshot"):
        raise HTTPException(status_code=400, detail="asset_type must be 'logo' or 'headshot'")
    url = body.url.strip()
    if len(url) > 2048:
        raise HTTPException(status_code=400, detail="That link is too long.")
    try:
        contents = safe_fetch.fetch(url, max_bytes=MAX_FILE_BYTES)
    except safe_fetch.FetchRefused as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    stored, ext, content_type = prepare_image(contents)
    result = store_branding_image(stored, ext, content_type, account_id, asset_type, None)
    return UploadResponse(url=result["url"], filename=f"imported.{ext}", size_bytes=result["size_bytes"])


@router.delete("/branding")
async def delete_branding_file(
    url: str,
    request: Request,
    account_id: str = Depends(require_account_id)
) -> DeleteResponse:
    """
    Delete a branding asset by URL.
    
    Only allows deletion of assets belonging to the current account.
    
    - **url**: The full URL of the asset to delete
    """
    # Security check: ensure URL contains the account_id
    if account_id not in url:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own branding assets"
        )
    
    success = await delete_branding_asset(url)
    
    if success:
        return DeleteResponse(ok=True, message="Asset deleted successfully")
    else:
        return DeleteResponse(ok=False, message="Asset not found or already deleted")

