"""
File upload routes for branding assets.

Pass B1.2: Upload API Endpoint
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from pydantic import BaseModel

from ..services.upload import upload_branding_asset, delete_branding_asset
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
    - **file**: Image file (PNG, JPEG, WebP, GIF; max 5MB; 100-2000px)
    
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

