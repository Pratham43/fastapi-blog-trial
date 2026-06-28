from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract base class for all storage providers."""

    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
    ) -> None:
        """
        Upload a file to the storage backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a file from the storage backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check whether an object exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        """
        Return the public URL for an object.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a temporary download URL.
        """
        raise NotImplementedError