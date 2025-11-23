"""
Document Storage Service for Loan Applications
Supports local storage and S3-compatible cloud storage with pre-signed URLs
"""
from __future__ import annotations

import os
import secrets
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timedelta
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.loan_application_document import LoanApplicationDocument, DocumentType
from ..schemas.loan_application_schemas import DocumentUploadRequest


# Configuration
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # 'local' or 's3'
LOCAL_STORAGE_PATH = Path("uploads/loan_documents")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
PRESIGNED_URL_EXPIRY = 3600  # 1 hour in seconds

# Ensure local storage directory exists
LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# S3 Configuration (if using cloud storage)
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "loan-documents")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")  # For S3-compatible services (MinIO, DigitalOcean Spaces, etc.)


class DocumentStorageService:
    """Service for managing document storage with pre-signed URLs"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_mode = STORAGE_MODE

        # Initialize S3 client if needed
        if self.storage_mode == "s3":
            try:
                import boto3
                from botocore.config import Config

                config = Config(signature_version='s3v4', region_name=S3_REGION)

                if S3_ENDPOINT:
                    self.s3_client = boto3.client(
                        's3',
                        endpoint_url=S3_ENDPOINT,
                        config=config
                    )
                else:
                    self.s3_client = boto3.client('s3', config=config)

                logger.info(f"Initialized S3 client for bucket: {S3_BUCKET}")
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise
        else:
            self.s3_client = None
            logger.info(f"Using local storage at: {LOCAL_STORAGE_PATH}")

    def _generate_file_key(self, application_id: UUID, doc_type: DocumentType, filename: str) -> str:
        """Generate unique storage key for file"""
        ext = Path(filename).suffix.lower()
        random_suffix = secrets.token_hex(8)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{application_id}/{doc_type.value}_{timestamp}_{random_suffix}{ext}"

    async def create_presigned_upload_url(
        self,
        application_id: UUID,
        request: DocumentUploadRequest,
        uploaded_by: UUID,
    ) -> Tuple[str, str, UUID]:
        """
        Create pre-signed URL for document upload

        Returns:
            Tuple of (upload_url, file_url, doc_id)
        """
        # Validate file size
        if request.file_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB")

        # Generate file key
        file_key = self._generate_file_key(application_id, request.doc_type, request.filename)

        if self.storage_mode == "s3":
            # Generate S3 pre-signed URL
            try:
                upload_url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': S3_BUCKET,
                        'Key': file_key,
                        'ContentType': request.content_type,
                    },
                    ExpiresIn=PRESIGNED_URL_EXPIRY
                )

                if S3_ENDPOINT:
                    file_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{file_key}"
                else:
                    file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"

            except Exception as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                raise RuntimeError(f"Failed to generate upload URL: {str(e)}")
        else:
            # For local storage, use a simple endpoint
            # In production, this would be handled by a separate upload endpoint
            file_url = f"/uploads/loan_documents/{file_key}"
            upload_url = f"/api/v1/loan-applications/documents/upload/{file_key}"

        # Create document record in DB (pending upload)
        doc = LoanApplicationDocument(
            application_id=application_id,
            uploaded_by=uploaded_by,
            doc_type=request.doc_type,
            file_url=file_url,
            file_name=request.filename,
            file_size=request.file_size,
            mime_type=request.content_type,
            meta_json={"pending": True, "file_key": file_key},
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(f"Created presigned URL for document {doc.id} ({request.doc_type.value})")
        return upload_url, file_url, doc.id

    async def confirm_upload(
        self,
        doc_id: UUID,
        file_hash: Optional[str] = None,
        meta_json: Optional[dict] = None,
    ) -> LoanApplicationDocument:
        """Confirm that file was successfully uploaded"""
        doc = await self.db.get(LoanApplicationDocument, doc_id)
        if not doc:
            raise ValueError("Document not found")

        # Update document metadata
        if file_hash:
            doc.file_hash = file_hash

        if meta_json:
            current_meta = doc.meta_json or {}
            current_meta.update(meta_json)
            doc.meta_json = current_meta

        # Mark as uploaded
        if doc.meta_json:
            doc.meta_json["pending"] = False

        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(f"Confirmed upload for document {doc_id}")
        return doc

    async def create_presigned_download_url(
        self,
        doc_id: UUID,
        expires_in: int = PRESIGNED_URL_EXPIRY,
    ) -> str:
        """Create pre-signed URL for document download"""
        doc = await self.db.get(LoanApplicationDocument, doc_id)
        if not doc:
            raise ValueError("Document not found")

        if self.storage_mode == "s3":
            # Extract S3 key from file_url
            file_key = doc.meta_json.get("file_key") if doc.meta_json else None
            if not file_key:
                # Parse from URL if not in metadata
                file_key = doc.file_url.split(f"{S3_BUCKET}/")[-1]

            try:
                download_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': S3_BUCKET,
                        'Key': file_key,
                    },
                    ExpiresIn=expires_in
                )
                return download_url
            except Exception as e:
                logger.error(f"Failed to generate download URL: {e}")
                raise RuntimeError(f"Failed to generate download URL: {str(e)}")
        else:
            # For local storage, return the file URL
            return doc.file_url

    async def delete_document(self, doc_id: UUID) -> bool:
        """Delete document from storage and database"""
        doc = await self.db.get(LoanApplicationDocument, doc_id)
        if not doc:
            return False

        if self.storage_mode == "s3":
            # Delete from S3
            file_key = doc.meta_json.get("file_key") if doc.meta_json else None
            if file_key:
                try:
                    self.s3_client.delete_object(Bucket=S3_BUCKET, Key=file_key)
                    logger.info(f"Deleted S3 object: {file_key}")
                except Exception as e:
                    logger.error(f"Failed to delete S3 object: {e}")
        else:
            # Delete from local storage
            try:
                file_key = doc.meta_json.get("file_key") if doc.meta_json else None
                if file_key:
                    file_path = LOCAL_STORAGE_PATH / file_key
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted local file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete local file: {e}")

        # Delete from database
        await self.db.delete(doc)
        await self.db.commit()

        logger.info(f"Deleted document {doc_id}")
        return True

    async def get_document(self, doc_id: UUID) -> Optional[LoanApplicationDocument]:
        """Get document by ID"""
        return await self.db.get(LoanApplicationDocument, doc_id)

    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()


# ============================================================================
# Local Storage Upload Handler
# ============================================================================

async def save_file_locally(file_key: str, file_content: bytes) -> str:
    """
    Save file to local storage
    This function would be called by the upload endpoint

    Args:
        file_key: Storage key for the file
        file_content: File binary content

    Returns:
        File URL
    """
    file_path = LOCAL_STORAGE_PATH / file_key

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info(f"Saved file locally: {file_path}")
    return f"/uploads/loan_documents/{file_key}"
