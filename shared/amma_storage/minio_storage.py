from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone
from typing import Any

from minio import Minio
from minio.error import S3Error


class MinioStorage:
    """Small S3-compatible storage helper for AMMA demo and future production use."""

    def __init__(self) -> None:
        endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        access_key = os.getenv("MINIO_ROOT_USER", "minio")
        secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minio123")
        secure = os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket: str) -> None:
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def ensure_project_buckets(self) -> list[str]:
        buckets = ["amma-receipts", "amma-reports", "amma-analytics-snapshots"]
        for bucket in buckets:
            self.ensure_bucket(bucket)
        return buckets

    def list_project_buckets(self) -> dict[str, list[str]]:
        self.ensure_project_buckets()
        result: dict[str, list[str]] = {}
        for bucket in ["amma-receipts", "amma-reports", "amma-analytics-snapshots"]:
            result[bucket] = [obj.object_name for obj in self.client.list_objects(bucket, recursive=True)]
        return result

    def put_bytes(self, bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> dict[str, Any]:
        self.ensure_bucket(bucket)
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return {
            "bucket": bucket,
            "object_name": object_name,
            "size_bytes": len(data),
            "content_type": content_type,
        }

    def put_text(self, bucket: str, object_name: str, text: str, content_type: str = "text/plain") -> dict[str, Any]:
        return self.put_bytes(bucket, object_name, text.encode("utf-8"), content_type=content_type)

    def put_json(self, bucket: str, object_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        return self.put_bytes(bucket, object_name, data, content_type="application/json")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
