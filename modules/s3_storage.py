import os
import boto3
from modules.utils import get_env

# Load Config
AWS_ACCESS_KEY = get_env("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = get_env("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = get_env("AWS_BUCKET_NAME")
AWS_REGION = get_env("AWS_REGION", "us-east-1")

def get_s3_client():
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY or not AWS_BUCKET_NAME:
        print("❌ CRITICAL: AWS Credentials or Bucket Name missing in .env")
        return None
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

def upload_to_s3(local_path: str, folder: str = "uploads") -> str | None:
    """
    Uploads a local file to S3 and returns the public URL.
    """
    if not local_path or not os.path.exists(local_path):
        print(f"⚠️ File not found for upload: {local_path}")
        return None

    s3 = get_s3_client()
    if not s3:
        return None

    file_name = os.path.basename(local_path)
    s3_key = f"{folder}/{file_name}"

    try:
        print(f"☁️ Uploading {file_name} to S3 bucket '{AWS_BUCKET_NAME}'...")
        s3.upload_file(
            local_path, 
            AWS_BUCKET_NAME, 
            s3_key, 
            ExtraArgs={'ContentType': _guess_content_type(file_name)}
        )
        
        # Construct URL (Assumes bucket allows public read or you use pre-signed URLs)
        # For private buckets, you'd generate a pre-signed URL here instead.
        url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✅ Uploaded: {url}")
        return url
    except Exception as e:
        print(f"❌ S3 Upload Failed: {e}")
        return None

def _guess_content_type(filename: str) -> str:
    if filename.endswith(".png"): return "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"): return "image/jpeg"
    if filename.endswith(".docx"): return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"