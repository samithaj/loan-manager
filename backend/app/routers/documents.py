from __future__ import annotations

import time
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.loan import Loan, Document
from app.models.client import Client
from loguru import logger


router = APIRouter(prefix="/v1")


# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# Pydantic models
class DocumentOut(BaseModel):
    id: str
    ownerType: str
    ownerId: str
    name: str
    mimeType: str
    size: int
    uploadedOn: str


def generate_document_id() -> str:
    return f"DOC-{int(time.time() * 1000)}"


# Client documents
@router.get("/clients/{clientId}/documents", response_model=list[DocumentOut])
async def list_client_documents(request: Request, clientId: str):
    async with SessionLocal() as session:
        # Verify client exists
        client = await session.get(Client, clientId)
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND"})

        query = select(Document).where(
            Document.owner_type == "CLIENT",
            Document.owner_id == clientId
        ).order_by(Document.uploaded_on.desc())
        rows = (await session.execute(query)).scalars().all()

        documents = [
            DocumentOut(
                id=d.id,
                ownerType=d.owner_type,
                ownerId=d.owner_id,
                name=d.name,
                mimeType=d.mime_type,
                size=d.size,
                uploadedOn=d.uploaded_on.isoformat()
            )
            for d in rows
        ]

        logger.bind(
            route=f"/clients/{clientId}/documents",
            method="GET",
            count=len(documents),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list client documents")

        return documents


@router.post("/clients/{clientId}/documents", status_code=201, response_model=DocumentOut)
async def upload_client_document(
    request: Request,
    clientId: str,
    file: UploadFile = File(...),
):
    async with SessionLocal() as session:
        # Verify client exists
        client = await session.get(Client, clientId)
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND"})

        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_TOO_LARGE", "message": f"File size exceeds {MAX_FILE_SIZE} bytes"}
            )

        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE_TYPE", "message": f"File type {file.content_type} not allowed"}
            )

        # Generate document ID and save file
        doc_id = generate_document_id()
        file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record
        document = Document(
            id=doc_id,
            owner_type="CLIENT",
            owner_id=clientId,
            name=file.filename or "unnamed",
            mime_type=file.content_type or "application/octet-stream",
            size=len(content)
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        logger.bind(
            route=f"/clients/{clientId}/documents",
            method="POST",
            documentId=document.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("uploaded client document")

        return DocumentOut(
            id=document.id,
            ownerType=document.owner_type,
            ownerId=document.owner_id,
            name=document.name,
            mimeType=document.mime_type,
            size=document.size,
            uploadedOn=document.uploaded_on.isoformat()
        )


# Loan documents
@router.get("/loans/{loanId}/documents", response_model=list[DocumentOut])
async def list_loan_documents(request: Request, loanId: str):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        query = select(Document).where(
            Document.owner_type == "LOAN",
            Document.owner_id == loanId
        ).order_by(Document.uploaded_on.desc())
        rows = (await session.execute(query)).scalars().all()

        documents = [
            DocumentOut(
                id=d.id,
                ownerType=d.owner_type,
                ownerId=d.owner_id,
                name=d.name,
                mimeType=d.mime_type,
                size=d.size,
                uploadedOn=d.uploaded_on.isoformat()
            )
            for d in rows
        ]

        logger.bind(
            route=f"/loans/{loanId}/documents",
            method="GET",
            count=len(documents),
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("list loan documents")

        return documents


@router.post("/loans/{loanId}/documents", status_code=201, response_model=DocumentOut)
async def upload_loan_document(
    request: Request,
    loanId: str,
    file: UploadFile = File(...),
):
    async with SessionLocal() as session:
        # Verify loan exists
        loan = await session.get(Loan, loanId)
        if not loan:
            raise HTTPException(status_code=404, detail={"code": "LOAN_NOT_FOUND"})

        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_TOO_LARGE", "message": f"File size exceeds {MAX_FILE_SIZE} bytes"}
            )

        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE_TYPE", "message": f"File type {file.content_type} not allowed"}
            )

        # Generate document ID and save file
        doc_id = generate_document_id()
        file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record
        document = Document(
            id=doc_id,
            owner_type="LOAN",
            owner_id=loanId,
            name=file.filename or "unnamed",
            mime_type=file.content_type or "application/octet-stream",
            size=len(content)
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        logger.bind(
            route=f"/loans/{loanId}/documents",
            method="POST",
            documentId=document.id,
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("uploaded loan document")

        return DocumentOut(
            id=document.id,
            ownerType=document.owner_type,
            ownerId=document.owner_id,
            name=document.name,
            mimeType=document.mime_type,
            size=document.size,
            uploadedOn=document.uploaded_on.isoformat()
        )


# Download document
@router.get("/documents/{documentId}/content")
async def download_document(request: Request, documentId: str):
    async with SessionLocal() as session:
        document = await session.get(Document, documentId)
        if not document:
            raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND"})

        # Find file on disk
        file_path = None
        for f in UPLOAD_DIR.glob(f"{documentId}_*"):
            file_path = f
            break

        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail={"code": "FILE_NOT_FOUND"})

        logger.bind(
            route=f"/documents/{documentId}/content",
            method="GET",
            correlationId=getattr(request.state, "correlation_id", None)
        ).info("downloaded document")

        return FileResponse(
            path=file_path,
            media_type=document.mime_type,
            filename=document.name
        )
