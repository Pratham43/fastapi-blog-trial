from io import BytesIO

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from starlette.concurrency import run_in_threadpool
from dataclasses import dataclass

from app.config import settings
from app.providers.storage.base import StorageProvider


@dataclass
class UploadedFile:
    key: str
    url: str

class CloudinaryStorageProvider(StorageProvider):
    """Cloudinary storage provider."""

    def __init__(self) -> None:

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=(
                settings.cloudinary_api_key.get_secret_value()
                if settings.cloudinary_api_key
                else None
            ),
            api_secret=(
                settings.cloudinary_api_secret.get_secret_value()
                if settings.cloudinary_api_secret
                else None
            ),
            secure=True,
        )


    def _upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
    ) -> None:

        return cloudinary.uploader.upload(
            BytesIO(file_bytes),
            public_id=key,
            overwrite=True,
            resource_type="image",
            folder=None,
        )

    async def upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
    ) -> UploadedFile:

        result = await run_in_threadpool(
            self._upload,
            file_bytes,
            key,
            content_type,
        )
        return UploadedFile(
            key=result["public_id"],
            url=result["secure_url"],
        )

    def _delete(self, key: str) -> None:

        cloudinary.uploader.destroy(
            key,
            resource_type="image",
        )

    async def delete(self, key: str) -> None:

        await run_in_threadpool(
            self._delete,
            key,
        )


    def _exists(self, key: str) -> bool:

        try:
            cloudinary.api.resource(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:

        return await run_in_threadpool(
            self._exists,
            key,
        )


    def get_public_url(self, key: str) -> str:

        url, _ = cloudinary.utils.cloudinary_url(
            key,
            secure=True,
        )

        return url


    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Cloudinary assets are already served through signed/public URLs.
        For public assets, simply return the asset URL.
        """

        return self.get_public_url(key)