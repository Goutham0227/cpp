"""
Amazon S3 Service Wrapper.
Handles invoice PDF storage and retrieval.
Falls back to local file system when USE_AWS is false.
"""

import os
import json
from datetime import datetime


class S3Service:
    """Wrapper for Amazon S3 with local filesystem fallback."""

    def __init__(self, use_aws=False, region="eu-west-1", bucket_name="timetracker-invoices-25167936"):
        self.use_aws = use_aws
        self.region = region
        self.bucket_name = bucket_name
        self._mock_storage = {}
        self._local_dir = os.path.join(os.path.dirname(__file__), "..", "local_storage")

        if self.use_aws:
            import boto3
            self.client = boto3.client("s3", region_name=region)
        else:
            self.client = None
            os.makedirs(self._local_dir, exist_ok=True)

    def upload_file(self, key: str, data: bytes, content_type: str = "application/pdf") -> dict:
        if self.use_aws:
            self.client.put_object(
                Bucket=self.bucket_name, Key=key, Body=data, ContentType=content_type
            )
            return {"bucket": self.bucket_name, "key": key, "url": f"s3://{self.bucket_name}/{key}"}
        else:
            self._mock_storage[key] = {
                "data": data,
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat(),
                "size": len(data),
            }
            local_path = os.path.join(self._local_dir, key.replace("/", "_"))
            with open(local_path, "wb") as f:
                f.write(data)
            return {"bucket": "local", "key": key, "url": f"file://{local_path}"}

    def download_file(self, key: str) -> bytes:
        if self.use_aws:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        else:
            if key in self._mock_storage:
                return self._mock_storage[key]["data"]
            return None

    def list_files(self, prefix: str = "") -> list:
        if self.use_aws:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        else:
            return [k for k in self._mock_storage.keys() if k.startswith(prefix)]

    def delete_file(self, key: str) -> bool:
        if self.use_aws:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        else:
            if key in self._mock_storage:
                del self._mock_storage[key]
                return True
            return False

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        if self.use_aws:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        else:
            return f"http://localhost:5000/mock-s3/{key}?expires={expires_in}"

    def get_status(self) -> dict:
        return {
            "service": "Amazon S3",
            "status": "available",
            "mode": "aws" if self.use_aws else "local_mock",
            "bucket": self.bucket_name,
            "files_stored": len(self._mock_storage) if not self.use_aws else "N/A",
        }
