from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings


class S3LetterStorage:
    def __init__(self, settings: Settings):
        if not settings.aws_s3_bucket:
            raise RuntimeError("AWS_S3_BUCKET is not configured.")
        self.bucket = settings.aws_s3_bucket
        self.settings = settings
        self.client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def save_pdf(self, doctor_id: str, pdf_bytes: bytes) -> str:
        key = f"letters/{doctor_id}/{uuid4().hex}.pdf"
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=pdf_bytes,
                ContentType="application/pdf",
                ServerSideEncryption="AES256",
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Unable to store the letter on secure storage.") from exc
        return key

    def create_download_url(self, storage_key: str, expires_in: int | None = None) -> str:
        expiry = expires_in or self.settings.s3_presign_expiry_seconds
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=expiry,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Unable to prepare a download link.") from exc

    def delete_pdf(self, storage_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=storage_key)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Unable to remove the letter file.") from exc


def build_s3_storage(settings: Settings) -> S3LetterStorage:
    return S3LetterStorage(settings)
