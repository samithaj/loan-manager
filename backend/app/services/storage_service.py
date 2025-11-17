from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from PIL import Image
import io
from loguru import logger


# Configuration
STORAGE_PATH = Path("uploads/bicycles")  # Local storage path
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
THUMBNAIL_SIZE = (300, 300)

# Ensure storage directory exists
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


async def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file.

    Args:
        file: Uploaded file

    Raises:
        ValueError: If file is invalid
    """
    # Check file extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB")

    # Reset file pointer for subsequent reads
    await file.seek(0)

    # Validate it's actually an image
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")

    # Reset file pointer again
    await file.seek(0)


async def upload_bicycle_image(file: UploadFile, bicycle_id: str) -> Tuple[str, str]:
    """
    Upload bicycle image and generate thumbnail.

    Args:
        file: Uploaded image file
        bicycle_id: ID of the bicycle

    Returns:
        Tuple of (image_url, thumbnail_url)
    """
    # Generate unique filename
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    random_suffix = secrets.token_hex(8)
    filename = f"{bicycle_id}_{random_suffix}{ext}"
    thumbnail_filename = f"{bicycle_id}_{random_suffix}_thumb{ext}"

    # Read file content
    content = await file.read()

    # Save original image
    image_path = STORAGE_PATH / filename
    with open(image_path, "wb") as f:
        f.write(content)

    # Generate and save thumbnail
    try:
        image = Image.open(io.BytesIO(content))

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background

        # Create thumbnail
        image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        # Save thumbnail
        thumbnail_path = STORAGE_PATH / thumbnail_filename
        image.save(thumbnail_path, quality=85, optimize=True)

        logger.info(f"Uploaded image: {filename}, thumbnail: {thumbnail_filename}")

    except Exception as e:
        # If thumbnail generation fails, clean up original and raise
        if image_path.exists():
            image_path.unlink()
        raise RuntimeError(f"Failed to generate thumbnail: {str(e)}")

    # Return URLs (in production, these would be full URLs with domain)
    # For now, return relative paths that can be served by FastAPI static files
    image_url = f"/uploads/bicycles/{filename}"
    thumbnail_url = f"/uploads/bicycles/{thumbnail_filename}"

    return image_url, thumbnail_url


async def delete_bicycle_image(image_url: str) -> bool:
    """
    Delete bicycle image from storage.

    Args:
        image_url: URL/path of the image to delete

    Returns:
        True if deleted successfully
    """
    try:
        # Extract filename from URL
        filename = Path(image_url).name

        # Delete main image
        image_path = STORAGE_PATH / filename
        if image_path.exists():
            image_path.unlink()
            logger.info(f"Deleted image: {filename}")

        # Delete thumbnail if exists
        thumb_filename = filename.replace(".", "_thumb.")
        thumbnail_path = STORAGE_PATH / thumb_filename
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            logger.info(f"Deleted thumbnail: {thumb_filename}")

        return True

    except Exception as e:
        logger.error(f"Failed to delete image {image_url}: {e}")
        return False


# ============================================================================
# S3/Cloud Storage Integration (Optional - for production)
# ============================================================================

"""
For production deployment with cloud storage (S3, Google Cloud Storage, etc.),
replace the local storage functions above with cloud storage SDK calls.

Example S3 implementation:

import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'bicycle-images')

async def upload_bicycle_image_s3(file: UploadFile, bicycle_id: str) -> Tuple[str, str]:
    # Generate unique filename
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    random_suffix = secrets.token_hex(8)
    filename = f"{bicycle_id}_{random_suffix}{ext}"
    thumbnail_filename = f"{bicycle_id}_{random_suffix}_thumb{ext}"

    # Read file content
    content = await file.read()

    # Upload original image to S3
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"bicycles/{filename}",
            Body=content,
            ContentType=file.content_type
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to upload to S3: {str(e)}")

    # Generate and upload thumbnail
    try:
        image = Image.open(io.BytesIO(content))
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background

        image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        thumb_buffer = io.BytesIO()
        image.save(thumb_buffer, format='JPEG', quality=85, optimize=True)
        thumb_buffer.seek(0)

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"bicycles/{thumbnail_filename}",
            Body=thumb_buffer,
            ContentType='image/jpeg'
        )
    except Exception as e:
        raise RuntimeError(f"Failed to generate/upload thumbnail: {str(e)}")

    # Return S3 URLs
    image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/bicycles/{filename}"
    thumbnail_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/bicycles/{thumbnail_filename}"

    return image_url, thumbnail_url

async def delete_bicycle_image_s3(image_url: str) -> bool:
    try:
        # Extract key from URL
        key = image_url.split('.com/')[-1]
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)

        # Delete thumbnail
        thumb_key = key.replace(".", "_thumb.")
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=thumb_key)

        return True
    except ClientError as e:
        logger.error(f"Failed to delete from S3: {e}")
        return False
"""
