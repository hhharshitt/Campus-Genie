"""
CampusGenie — Documents API Routes
Handles PDF upload, listing, and deletion.

POST   /api/documents/upload     — Upload + index a PDF
GET    /api/documents/           — List all indexed documents
DELETE /api/documents/{doc_id}   — Remove a document
"""

import os
import shutil
import logging
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.rag.pipeline import get_pipeline, RAGPipeline
from app.models.schemas import DocumentInfo, DocumentListResponse, DeleteDocumentResponse
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf"}


def _validate_pdf(file: UploadFile):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are accepted. Got: {file.filename}",
        )


def _save_upload(file: UploadFile) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    save_path = os.path.join(settings.upload_dir, file.filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)
    if file_size_mb > settings.max_upload_size_mb:
        os.remove(save_path)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f} MB). Max: {settings.max_upload_size_mb} MB",
        )
    return save_path


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """Upload and index a PDF document. Returns doc metadata + chunk count."""
    _validate_pdf(file)
    filepath = _save_upload(file)

    try:
        result = pipeline.index_document(filepath)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Indexing failed for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    return DocumentInfo(
        doc_id=result.doc_id,
        filename=result.filename,
        page_count=result.page_count,
        chunk_count=result.chunk_count,
        uploaded_at=result.indexed_at,
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(pipeline: RAGPipeline = Depends(get_pipeline)):
    """List all indexed documents with chunk counts."""
    docs_raw = pipeline.list_documents()
    docs = [
        DocumentInfo(
            doc_id=d["doc_id"],
            filename=d["filename"],
            page_count=0,
            chunk_count=d["chunk_count"],
            uploaded_at=datetime.utcnow(),
        )
        for d in docs_raw
    ]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    doc_id: str,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """Remove a document and all its chunks from the vector store."""
    if not pipeline.document_exists(doc_id):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    deleted = pipeline.delete_document(doc_id)
    return DeleteDocumentResponse(
        success=True,
        message=f"Deleted {deleted} chunks for document '{doc_id}'",
    )
