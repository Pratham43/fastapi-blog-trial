from functools import lru_cache

from app.config import settings
from app.providers.storage.base import StorageProvider
from app.providers.storage.s3 import S3StorageProvider
from enum import StrEnum


class StorageProviderType(StrEnum):
    S3 = "s3"
    CLOUDINARY = "cloudinary"
    LOCAL = "local"

@lru_cache(maxsize=1)
def get_storage() -> StorageProvider:
    """
    Returns the configured storage provider.

    The instance is cached so the boto3 client is only created once.
    """

    provider = settings.storage_provider.lower()

    if provider == "s3":
        return S3StorageProvider()

    raise ValueError(
        f"Unsupported storage provider: {provider}"
    )