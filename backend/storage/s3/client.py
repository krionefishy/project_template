import asyncio
import re
from typing import Any

import boto3
from botocore.client import Config


def sanitize_key_segment(segment: str) -> str:
    """Remove characters unsafe for S3 key segments."""
    return re.sub(r"[^\w.\-]", "_", segment)


class S3Client:
    """
    Async-friendly wrapper around boto3 S3.
    All blocking calls are offloaded to a thread via asyncio.to_thread.

    Supports Yandex Cloud / Cloud.ru tenant-prefixed credentials:
        access_key = f"{tenant_id}:{key_id}"
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "ru-central-1",
        verify: bool = True,
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            verify=verify,  # False for MinIO / self-signed certs
            config=Config(s3={"addressing_style": "path"}),
        )

    def _put_object(self, key: str, body: bytes, content_type: str, metadata: dict[str, str]) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            Metadata={k: v.encode("ascii", errors="replace").decode() for k, v in metadata.items()},
        )

    async def put_object(
        self,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        await asyncio.to_thread(self._put_object, key, body, content_type, metadata or {})

    def _delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    async def delete_object(self, key: str) -> None:
        await asyncio.to_thread(self._delete_object, key)

    def _delete_objects(self, keys: list[str]) -> None:
        self._client.delete_objects(
            Bucket=self._bucket,
            Delete={"Objects": [{"Key": k} for k in keys]},
        )

    async def delete_objects(self, keys: list[str]) -> None:
        if keys:
            await asyncio.to_thread(self._delete_objects, keys)

    def _generate_presigned_url(self, key: str, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._generate_presigned_url(key, expires_in)

    def _head_object(self, key: str) -> dict[str, Any]:
        return self._client.head_object(Bucket=self._bucket, Key=key)

    async def object_exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self._head_object, key)
            return True
        except Exception:
            return False
