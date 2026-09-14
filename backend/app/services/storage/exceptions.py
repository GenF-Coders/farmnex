from __future__ import annotations


class StorageError(Exception):
    """Base exception for FarmNex storage failures."""


class StorageConfigurationError(StorageError):
    """Storage is not configured correctly."""


class StorageValidationError(StorageError):
    """The requested storage operation failed validation."""


class StorageProviderError(StorageError):
    """The external storage provider returned an error."""


class StorageNotFoundError(StorageError):
    """The requested storage object does not exist."""
