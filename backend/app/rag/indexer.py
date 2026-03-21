"""
CampusGenie — Document Indexer
Orchestrates the full ingestion pipeline:
  PDF file → extract text → chunk → embed → store in ChromaDB

This is the "admin upload" step of the RAG architecture.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from app.rag.pdf_processor import PDFProcessor
from app.rag.chunker import TextChunker
from app.rag.embeddings import get_embedding_engine
from app.rag.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)


class IndexingResult:
    """Metadata returned after a successful document indexing run."""

    def __init__(
        self,
        doc_id: str,
        filename: str,
        page_count: int,
        chunk_count: int,
        indexed_at: datetime,
    ):
        self.doc_id = doc_id
        self.filename = filename
        self.page_count = page_count
        self.chunk_count = chunk_count
        self.indexed_at = indexed_at


class DocumentIndexer:
    """
    High-level pipeline that ingests a PDF and indexes it into ChromaDB.

    Usage:
        indexer = DocumentIndexer()
        result = indexer.index(filepath="/app/uploads/syllabus.pdf")
    """

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedding_engine = get_embedding_engine()
        self.vector_store = VectorStore()

    def index(self, filepath: str, doc_id: Optional[str] = None) -> IndexingResult:
        """
        Full ingestion pipeline for a single PDF.

        Steps:
          1. Extract text per page (PyMuPDF)
          2. Split into overlapping chunks
          3. Embed each chunk (sentence-transformers)
          4. Store vectors + metadata in ChromaDB

        Args:
            filepath: Absolute path to the PDF file
            doc_id:   Optional custom doc_id (auto-generated if not provided)

        Returns:
            IndexingResult with counts and metadata
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)

        # Auto-generate doc_id if not provided
        if doc_id is None:
            doc_id = self._make_doc_id(filename)

        logger.info(f"Starting indexing: {filename} (doc_id={doc_id})")

        # ── Step 1: Extract text from PDF ─────────────────────────────────────
        doc_content = self.pdf_processor.process(filepath, doc_id=doc_id)
        logger.info(
            f"PDF extracted: {doc_content.page_count} pages, "
            f"{doc_content.total_words} words"
        )

        # ── Step 2: Chunk the text ────────────────────────────────────────────
        chunks = self.chunker.chunk_document(doc_content)
        logger.info(f"Chunked into {len(chunks)} pieces")

        if not chunks:
            raise ValueError(f"No text content extracted from {filename}")

        # ── Step 3: Embed all chunks ──────────────────────────────────────────
        embeddings = self.embedding_engine.embed_chunks(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # ── Step 4: Store in ChromaDB ─────────────────────────────────────────
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info(f"Indexed {len(chunks)} chunks into ChromaDB ✓")

        return IndexingResult(
            doc_id=doc_id,
            filename=filename,
            page_count=doc_content.page_count,
            chunk_count=len(chunks),
            indexed_at=datetime.utcnow(),
        )

    def delete(self, doc_id: str) -> int:
        """
        Remove all chunks for a document from ChromaDB.

        Returns:
            Number of chunks deleted
        """
        deleted = self.vector_store.delete_document(doc_id)
        logger.info(f"Deleted {deleted} chunks for doc_id={doc_id}")
        return deleted

    def is_indexed(self, doc_id: str) -> bool:
        """Check if a document is already in the vector store."""
        return self.vector_store.document_exists(doc_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_doc_id(filename: str) -> str:
        """Deterministic doc_id from filename (no random suffix needed)."""
        import re
        name = os.path.splitext(filename)[0]
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name).lower()
        return safe[:60]
