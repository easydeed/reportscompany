#!/usr/bin/env python3
"""
Upload Seller Report Assets to Cloudflare R2

This script uploads the extracted seller_report_assets folder to R2 with the correct
directory structure for the property reports wizard.

Usage:
    python scripts/upload_seller_assets_to_r2.py

Environment variables required:
    R2_ACCOUNT_ID - Cloudflare account ID
    R2_ACCESS_KEY_ID - R2 access key
    R2_SECRET_ACCESS_KEY - R2 secret key
    R2_BUCKET_NAME - Bucket name (default: market-reports)

Expected folder structure after upload:
    r2://market-reports/property-reports/
    ├── previews/
    │   ├── 1.jpg, 2.jpg, 3.jpg, 4.jpg, 5.jpg  (theme thumbnails)
    │   ├── 1/                                   (Theme 1: page previews)
    │   │   ├── 1.jpg through 20.jpg
    │   ├── 2/                                   (Theme 2: page previews)
    │   │   ├── 1.jpg through 21.jpg
    │   ├── 3/                                   (Theme 3: page previews)
    │   │   ├── 1.jpg through 18.jpg
    │   ├── 4/                                   (Theme 4: page previews)
    │   │   ├── 1.jpg through 7.jpg
    │   └── 5/                                   (Theme 5: page previews)
    │       ├── 1.jpg through 8.jpg
    ├── css/
    │   ├── main.css, style.css, bootstrap.min.css
    │   └── theme_2/style.css, theme_3/style.css, etc.
    ├── fonts/
    │   ├── bariol_*.woff2, bariol_*.woff
    │   ├── Nexa*.woff
    │   └── Montserrat-*.otf
    └── images/
        ├── 1/, 2/, ..., 20/  (page-specific images)
        ├── theme_2/, theme_4/, theme_5/  (theme-specific images)
        └── icons (bed.png, sqr_feet.png, etc.)
"""

import os
import sys
import mimetypes
from pathlib import Path
from typing import Optional

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("Error: boto3 required. Install with: pip install boto3")
    sys.exit(1)

# Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# Source and destination paths
SOURCE_DIR = Path(__file__).parent.parent / "seller_report_assets"
R2_PREFIX = "property-reports"


def get_r2_client():
    """Create and return R2 client."""
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise RuntimeError(
            "Missing R2 credentials. Set: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY"
        )
    
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def get_content_type(filepath: Path) -> str:
    """Get MIME type for file."""
    mime_type, _ = mimetypes.guess_type(str(filepath))
    
    # Custom mappings for web fonts
    ext = filepath.suffix.lower()
    if ext == ".woff2":
        return "font/woff2"
    elif ext == ".woff":
        return "font/woff"
    elif ext == ".otf":
        return "font/otf"
    elif ext == ".ttf":
        return "font/ttf"
    elif ext == ".eot":
        return "application/vnd.ms-fontobject"
    
    return mime_type or "application/octet-stream"


def upload_file(client, local_path: Path, r2_key: str, dry_run: bool = False) -> bool:
    """Upload a single file to R2."""
    content_type = get_content_type(local_path)
    
    if dry_run:
        print(f"  [DRY RUN] Would upload: {r2_key} ({content_type})")
        return True
    
    try:
        with open(local_path, "rb") as f:
            client.upload_fileobj(
                f,
                R2_BUCKET_NAME,
                r2_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "CacheControl": "public, max-age=31536000",  # 1 year cache
                },
            )
        print(f"  [OK] {r2_key}")
        return True
    except Exception as e:
        print(f"  [FAIL] {r2_key}: {e}")
        return False


def upload_directory(
    client,
    source_dir: Path,
    r2_prefix: str,
    dry_run: bool = False,
    extensions: Optional[set] = None,
) -> tuple[int, int]:
    """
    Recursively upload a directory to R2.
    
    Args:
        client: R2 client
        source_dir: Local directory to upload
        r2_prefix: R2 key prefix (e.g., "property-reports/fonts")
        dry_run: If True, only print what would be uploaded
        extensions: Set of allowed extensions (e.g., {".jpg", ".png"}). None = all.
    
    Returns:
        Tuple of (success_count, total_count)
    """
    success = 0
    total = 0
    
    for file_path in source_dir.rglob("*"):
        if not file_path.is_file():
            continue
        
        # Skip hidden files and shortcuts
        if file_path.name.startswith(".") or file_path.suffix.lower() == ".lnk":
            continue
        
        # Filter by extension if specified
        if extensions and file_path.suffix.lower() not in extensions:
            continue
        
        # Build R2 key
        relative_path = file_path.relative_to(source_dir)
        r2_key = f"{r2_prefix}/{relative_path.as_posix()}"
        
        total += 1
        if upload_file(client, file_path, r2_key, dry_run):
            success += 1
    
    return success, total


def main():
    """Main upload function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload seller assets to R2")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be uploaded")
    args = parser.parse_args()
    
    if not SOURCE_DIR.exists():
        print(f"Error: Source directory not found: {SOURCE_DIR}")
        print("Run from repo root with: python scripts/upload_seller_assets_to_r2.py")
        sys.exit(1)
    
    print(f"Source: {SOURCE_DIR}")
    print(f"Destination: s3://{R2_BUCKET_NAME}/{R2_PREFIX}/")
    print()
    
    if args.dry_run:
        print("=== DRY RUN MODE ===")
        print()
    
    client = get_r2_client()
    total_success = 0
    total_files = 0
    
    # 1. Upload fonts
    print("[1/5] Uploading fonts...")
    fonts_dir = SOURCE_DIR / "fonts"
    if fonts_dir.exists():
        s, t = upload_directory(
            client,
            fonts_dir,
            f"{R2_PREFIX}/fonts",
            dry_run=args.dry_run,
            extensions={".woff", ".woff2", ".otf", ".ttf", ".eot"},
        )
        total_success += s
        total_files += t
        print(f"   Fonts: {s}/{t} uploaded")
    print()
    
    # 2. Upload CSS
    print("[2/5] Uploading CSS...")
    css_dir = SOURCE_DIR / "css"
    if css_dir.exists():
        s, t = upload_directory(
            client,
            css_dir,
            f"{R2_PREFIX}/css",
            dry_run=args.dry_run,
            extensions={".css"},
        )
        total_success += s
        total_files += t
        print(f"   CSS: {s}/{t} uploaded")
    print()
    
    # 3. Upload images (main images folder)
    print("[3/5] Uploading images...")
    images_dir = SOURCE_DIR / "images"
    if images_dir.exists():
        s, t = upload_directory(
            client,
            images_dir,
            f"{R2_PREFIX}/images",
            dry_run=args.dry_run,
            extensions={".jpg", ".jpeg", ".png", ".svg", ".gif", ".webp"},
        )
        total_success += s
        total_files += t
        print(f"   Images: {s}/{t} uploaded")
    print()
    
    # 4. Upload theme-specific assets
    for theme_num in [2, 3, 4, 5]:
        theme_dir = SOURCE_DIR / f"theme_{theme_num}"
        if theme_dir.exists():
            print(f"[4/5] Uploading theme_{theme_num} assets...")
            
            # Upload images
            img_dirs = [theme_dir / "images", theme_dir / "img"]
            for img_dir in img_dirs:
                if img_dir.exists():
                    s, t = upload_directory(
                        client,
                        img_dir,
                        f"{R2_PREFIX}/images/theme_{theme_num}",
                        dry_run=args.dry_run,
                        extensions={".jpg", ".jpeg", ".png", ".svg"},
                    )
                    total_success += s
                    total_files += t
            
            # Upload CSS
            css_files = list(theme_dir.glob("*.css")) + list((theme_dir / "css").glob("*.css") if (theme_dir / "css").exists() else [])
            for css_file in css_files:
                r2_key = f"{R2_PREFIX}/css/theme_{theme_num}_{css_file.name}"
                total_files += 1
                if upload_file(client, css_file, r2_key, args.dry_run):
                    total_success += 1
            
            print(f"   Theme {theme_num}: uploaded")
    print()
    
    # Summary
    print("=" * 50)
    print(f"Total: {total_success}/{total_files} files uploaded successfully")
    
    if not args.dry_run:
        print()
        print("Assets are now available at:")
        print(f"  https://assets.trendyreports.com/{R2_PREFIX}/")
        print()
        print("Next steps:")
        print("  1. Generate page preview screenshots and upload to /previews/")
        print("  2. Update ThemeSelector to use real images")
    
    return 0 if total_success == total_files else 1


if __name__ == "__main__":
    sys.exit(main())

