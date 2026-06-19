from typing import Any
from uuid import uuid4

from backend.storage.s3.client import S3Client


class MockS3Client(S3Client):
    """
    In-memory S3 client for tests.

    Tracks all operations (put, delete, presign) in self.operations.
    Stores uploaded content in self._uploads for assertion.

    Usage in tests:
        mock_s3.was_operation_performed("put_object", key="examples/...")
        content = mock_s3.get_uploaded_content("my/key")
        ops = mock_s3.get_operations_by_type("delete_object")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Skip real S3Client.__init__ — no boto3 client created
        self.operations: list[dict[str, Any]] = []
        self._uploads: dict[str, bytes] = {}
        self._bucket = kwargs.get("bucket", "test-bucket")
        self._endpoint_url = kwargs.get("endpoint_url", "http://localhost:9000")

    # --- Core operations ---

    async def put_object(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.operations.append({
            "operation": "put_object",
            "key": key,
            "content_type": content_type,
            "size": len(body),
            "metadata": metadata or {},
        })
        self._uploads[key] = body

    async def delete_object(self, key: str) -> None:
        self.operations.append({"operation": "delete_object", "key": key})
        self._uploads.pop(key, None)

    async def delete_objects(self, keys: list[str]) -> None:
        for key in keys:
            await self.delete_object(key)

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        self.operations.append({
            "operation": "presigned_url",
            "key": key,
            "expires_in": expires_in,
        })
        return f"{self._endpoint_url}/{self._bucket}/{key}?X-Amz-Signature={uuid4()}"

    async def object_exists(self, key: str) -> bool:
        return key in self._uploads

    # --- Assertion helpers ---

    def get_uploaded_content(self, key: str) -> bytes | None:
        """Return raw bytes stored for *key*, or None if not uploaded."""
        return self._uploads.get(key)

    def get_operations_by_type(self, operation: str) -> list[dict[str, Any]]:
        """Return all recorded operations of the given type."""
        return [op for op in self.operations if op.get("operation") == operation]

    def was_operation_performed(self, operation: str, key: str | None = None) -> bool:
        """Return True if the operation was performed, optionally filtered by key."""
        for op in self.operations:
            if op.get("operation") == operation:
                if key is None or op.get("key") == key:
                    return True
        return False

    def clear_all(self) -> None:
        self.operations.clear()
        self._uploads.clear()
