import asyncio
from unittest.mock import Mock

from botocore.exceptions import ClientError
from fastapi import HTTPException
import pytest

from api.services import upload


@pytest.fixture
def storage(monkeypatch):
    client = Mock()
    monkeypatch.setattr(upload, "R2_PUBLIC_URL", "https://cdn.example.test/assets")
    monkeypatch.setattr(upload, "R2_ACCOUNT_ID", "test-account")
    monkeypatch.setattr(upload, "R2_BUCKET_NAME", "assets")
    monkeypatch.setattr(upload, "get_r2_client", lambda: client)
    return client


@pytest.mark.parametrize("root", [
    "https://cdn.example.test/assets",
    "https://test-account.r2.cloudflarestorage.com/assets",
    "https://assets.test-account.r2.cloudflarestorage.com",
])
def test_deletes_the_owned_object(storage, root):
    key = "branding/account-one/logo_20260101120000_abcdef12.png"
    assert asyncio.run(upload.delete_branding_asset(f"{root}/{key}?version=1", "account-one"))
    storage.head_object.assert_called_once_with(Bucket="assets", Key=key)
    storage.delete_object.assert_called_once_with(Bucket="assets", Key=key)


@pytest.mark.parametrize("url", [
    "https://cdn.example.test/assets/branding/account-two/logo.png",
    "https://unconfigured.example.test/branding/account-one/logo.png",
    "invalid",
])
def test_refuses_unowned_or_unknown_object_before_storage(storage, url):
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload.delete_branding_asset(url, "account-one"))
    assert error.value.status_code == 403
    assert storage.mock_calls == []


def test_missing_object_is_distinct_from_storage_failure(storage):
    url = "https://cdn.example.test/assets/branding/account-one/logo.png"
    storage.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
    assert not asyncio.run(upload.delete_branding_asset(url, "account-one"))
    storage.head_object.side_effect = ClientError({"Error": {"Code": "AccessDenied"}}, "HeadObject")
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload.delete_branding_asset(url, "account-one"))
    assert error.value.status_code == 502
    storage.delete_object.assert_not_called()
