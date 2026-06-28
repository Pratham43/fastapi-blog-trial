from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.providers.storage.base import StorageProvider


class S3StorageProvider(StorageProvider):
    """Generic S3-compatible storage provider.

    Works with:
    - AWS S3
    - Backblaze B2
    - MinIO
    - DigitalOcean Spaces
    """

    def __init__(self) -> None:
        self.bucket = settings.s3_bucket_name

        self.client = boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=(
                settings.s3_access_key_id.get_secret_value()
                if settings.s3_access_key_id
                else None
            ),
            aws_secret_access_key=(
                settings.s3_secret_access_key.get_secret_value()
                if settings.s3_secret_access_key
                else None
            ),
        )

    def _upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
    ) -> None:
        self.client.upload_fileobj(
            Fileobj=BytesIO(file_bytes),
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    async def upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
    ) -> None:
        await run_in_threadpool(
            self._upload,
            file_bytes,
            key,
            content_type,
        )


    def _delete(self, key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    async def delete(self, key: str) -> None:
        await run_in_threadpool(
            self._delete,
            key,
        )

    def _exists(self, key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]

            if error_code in ("404", "NoSuchKey"):
                return False

            raise

    async def exists(self, key: str) -> bool:
        return await run_in_threadpool(
            self._exists,
            key,
        )

    def get_public_url(self, key: str) -> str:
        """
        Returns the public URL of an object.

        Example:
        https://f005.backblazeb2.com/file/my-bucket/profile_pics/abc.jpg
        """

        if settings.s3_public_url:
            return f"{settings.s3_public_url.rstrip('/')}/{key}"

        return (
            f"{settings.s3_endpoint_url.rstrip('/')}"
            f"/{self.bucket}/{key}"
        )


    def _generate_presigned_url(
        self,
        key: str,
        expires_in: int,
    ) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return await run_in_threadpool(
            self._generate_presigned_url,
            key,
            expires_in,
        )