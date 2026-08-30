import os
from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalDiskStorage(StorageBackend):
    """Zero-setup backend for local dev/demo - no external service required.
    Not what you'd run in production; use S3Storage for that."""

    def __init__(self, root: str = "./blob_storage"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # keys are our own generated UUIDs (see main.py), never user input - safe to join directly.
        return self.root / key

    def put(self, key: str, data: bytes) -> None:
        self._path(key).write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage(StorageBackend):
    """MinIO or AWS S3, via boto3. Point S3_ENDPOINT_URL at a MinIO instance for on-prem/local,
    or leave it unset to hit real AWS S3."""

    def __init__(self):
        import boto3
        self.bucket = os.environ["S3_BUCKET"]
        self.client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),  for MinIO
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
        )

    def put(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


def get_storage() -> StorageBackend:
    backend = os.environ.get("STORAGE_BACKEND", "local")
    if backend == "s3":
        return S3Storage()
    return LocalDiskStorage(os.environ.get("LOCAL_STORAGE_ROOT", "./blob_storage"))
