"""S3 backup utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import boto3


def upload_file(path: Path, bucket: str, key: Optional[str] = None) -> None:
    """Upload a file to an S3 bucket.

    Parameters
    ----------
    path: Path
        Local file path to upload.
    bucket: str
        S3 bucket name.
    key: str | None
        Key under which to store the file. Defaults to the filename.
    """
    key = key or path.name
    if not path.exists():
        raise FileNotFoundError(path)
    s3 = boto3.client("s3")
    s3.upload_file(str(path), bucket, key)
