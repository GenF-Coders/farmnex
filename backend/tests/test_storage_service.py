from __future__ import annotations

import pytest

from app.services.storage_service import StorageService, StorageValidationError


def test_validate_bucket() -> None:
    assert StorageService.validate_bucket("storage-bucket") == "storage-bucket"
    with pytest.raises(StorageValidationError):
        StorageService.validate_bucket("storage-bucket/path")


def test_validate_flat_path() -> None:
    assert StorageService.validate_path("profile_image/test.webp") == "profile_image/test.webp"
    for invalid in ("/profile_image/a.webp", "profile_image/../a.webp", "profile_image\\a.webp", "profile_image//a.webp"):
        with pytest.raises(StorageValidationError):
            StorageService.validate_path(invalid)


def test_validate_image_signatures() -> None:
    StorageService.validate_file_signature(
        file_bytes=b"\x89PNG\r\n\x1a\nrest",
        content_type="image/png",
    )
    StorageService.validate_file_signature(
        file_bytes=b"RIFF0000WEBPdata",
        content_type="image/webp",
    )
    StorageService.validate_file_signature(
        file_bytes=b"%PDF-1.7\nrest",
        content_type="application/pdf",
    )
    with pytest.raises(StorageValidationError):
        StorageService.validate_file_signature(
            file_bytes=b"not-a-png",
            content_type="image/png",
        )
