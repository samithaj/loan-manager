from __future__ import annotations

import uuid
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import SessionLocal
from ..models.loan import Document
from ..config import get_settings


router = APIRouter(prefix="/v1", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    ownerType: str
    ownerId: str
    name: str
    mimeType: str
    size: int
    uploadedOn: str  # ISO datetime string


# Allowed MIME types for security
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}

# Maximum file size (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024


def get_upload_dir() -> str:
    """Get the upload directory, create if it doesn't exist"""
    upload_dir = "/tmp/loan_manager_uploads"  # In production, use proper storage
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def get_file_path(document_id: str, filename: str) -> str:
    """Get the full file path for a document"""
    upload_dir = get_upload_dir()
    # Use document ID as subdirectory for organization
    doc_dir = os.path.join(upload_dir, document_id)
    os.makedirs(doc_dir, exist_ok=True)
    return os.path.join(doc_dir, filename)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    owner_type: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List documents with optional filtering"""
    async with SessionLocal() as session:  # type: AsyncSession
        stmt = select(Document).order_by(Document.uploaded_on.desc()).offset(skip).limit(limit)
        
        if owner_type:
            stmt = stmt.where(Document.owner_type == owner_type)
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
        
        result = await session.execute(stmt)
        documents = result.scalars().all()
        
        return [
            DocumentOut(
                id=doc.id,
                ownerType=doc.owner_type,
                ownerId=doc.owner_id,
                name=doc.name,
                mimeType=doc.mime_type,
                size=doc.size,
                uploadedOn=doc.uploaded_on.isoformat()
            )
            for doc in documents
        ]


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    owner_type: str = Form(...),
    owner_id: str = Form(...)
):
    """Upload a document"""
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}")
    
    # Validate owner type
    if owner_type not in ["CLIENT", "LOAN"]:
        raise HTTPException(status_code=400, detail="Owner type must be CLIENT or LOAN")
    
    async with SessionLocal() as session:  # type: AsyncSession
        # Read file content
        content = await file.read()
        actual_size = len(content)
        
        if actual_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Create document record
        document = Document(
            id=str(uuid.uuid4()),
            owner_type=owner_type,
            owner_id=owner_id,
            name=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            size=actual_size,
            uploaded_on=datetime.utcnow()
        )
        
        # Save file to disk
        file_path = get_file_path(document.id, document.name)
        with open(file_path, "wb") as f:
            f.write(content)
        
        session.add(document)
        await session.commit()
        await session.refresh(document)
        
        return DocumentOut(
            id=document.id,
            ownerType=document.owner_type,
            ownerId=document.owner_id,
            name=document.name,
            mimeType=document.mime_type,
            size=document.size,
            uploadedOn=document.uploaded_on.isoformat()
        )


@router.get("/documents/{document_id}")
async def download_document(document_id: str):
    """Download a document"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = get_file_path(document.id, document.name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=file_path,
            filename=document.name,
            media_type=document.mime_type
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    async with SessionLocal() as session:  # type: AsyncSession
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from disk
        file_path = get_file_path(document.id, document.name)
        if os.path.exists(file_path):
            os.remove(file_path)
            # Try to remove the directory if empty
            try:
                doc_dir = os.path.dirname(file_path)
                os.rmdir(doc_dir)
            except OSError:
                pass  # Directory not empty, that's fine
        
        await session.delete(document)
        await session.commit()
        
        return {"message": "Document deleted"}