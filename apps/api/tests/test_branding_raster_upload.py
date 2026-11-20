import asyncio
from io import BytesIO
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

from api.services import upload


def raster(kind):
    buf = BytesIO()
    Image.new("RGB", (120, 110), "white").save(buf, format=kind)
    return buf.getvalue()


def submit(data, filename, mime):
    return asyncio.run(upload.upload_branding_asset(
        UploadFile(file=BytesIO(data), filename=filename, headers=Headers({"content-type": mime})),
        "pilot-account", "logo"))


@pytest.mark.parametrize(("kind", "ext", "mime"), [
    ("PNG", "png", "image/png"), ("JPEG", "jpg", "image/jpeg"),
    ("GIF", "gif", "image/gif"), ("WEBP", "webp", "image/webp"),
])
def test_approved_image_keeps_its_storage_type(monkeypatch, kind, ext, mime):
    store = Mock()
    monkeypatch.setattr(upload, "get_r2_client", lambda: store)
    monkeypatch.setattr(upload, "R2_PUBLIC_URL", "https://assets.example.test")
    data = raster(kind)
    result = submit(data, f"brand.{ext}", mime)
    stored = store.put_object.call_args.kwargs
    assert stored["ContentType"] == mime
    assert stored["Body"] == data
    assert result["url"].endswith(stored["Key"]) and stored["Key"].endswith("." + ext)


@pytest.mark.parametrize(("data", "filename", "mime"), [
    (b"plain text", "logo.png", "image/png"), (b"<svg/>", "logo.svg", "image/svg+xml"),
    (raster("PNG"), "logo.jpg", "image/png"), (raster("PNG"), "logo.jpg", "image/jpeg"),
    (raster("JPEG")[:25], "logo.jpg", "image/jpeg"), (bytes(5 * 1024 * 1024 + 1), "large.png", "image/png"),
], ids=["plain-text", "vector", "wrong-extension", "wrong-type", "truncated", "size-limit"])
def test_refused_upload_never_reaches_storage(monkeypatch, data, filename, mime):
    get_storage = Mock()
    monkeypatch.setattr(upload, "get_r2_client", get_storage)
    with pytest.raises(HTTPException) as failure:
        submit(data, filename, mime)
    assert failure.value.status_code == 400
    get_storage.assert_not_called()

def test_unapproved_container_variant_has_a_client_error(monkeypatch):
    from unittest.mock import MagicMock
    image = MagicMock()
    image.__enter__.return_value.format = "MPO"
    monkeypatch.setattr(upload.Image, "open", lambda *args, **kwargs: image)
    store = Mock()
    monkeypatch.setattr(upload, "get_r2_client", store)
    with pytest.raises(HTTPException) as failure:
        submit(b"test-image", "camera.jpg", "image/jpeg")
    assert failure.value.status_code == 400
    store.assert_not_called()
