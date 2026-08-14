from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """
    Abstract interface for object storage operations.
    Supports local filesystem storage in development and S3-compatible storage in production.
    """

    @abstractmethod
    async def upload_file(self, file_bytes: bytes, destination_key: str, content_type: str = "application/octet-stream") -> str:
        """Upload raw file bytes to storage and return storage key/URI."""
        pass

    @abstractmethod
    async def download_file(self, file_key: str) -> bytes:
        """Download raw file bytes from storage given a file key."""
        pass

    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def exists(self, file_key: str) -> bool:
        """Check if a file exists in storage."""
        pass
