"""
CampusGenie — PDF Processor
Extracts text and metadata from uploaded PDF files using PyMuPDF (fitz).
Returns structured page-level data for the chunking pipeline.
"""

import fitz  # PyMuPDF
import os
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PageContent:
    """Text content extracted from a single PDF page."""
    page_number: int    # 1-indexed
    text: str
    word_count: int


@dataclass
class DocumentContent:
    """Extracted content from an entire PDF document."""
    filename: str
    doc_id: str
    page_count: int
    pages: list[PageContent]
    total_words: int


class PDFProcessor:
    """
    Extracts text from PDF files page by page using PyMuPDF.

    Preserves page numbers so the RAG pipeline can include
    accurate page-level citations in responses.

    Text extraction strategy:
    - Uses fitz "text" mode (plain text with newlines)
    - Cleans excessive whitespace while preserving paragraph breaks
    - Filters pages with fewer than min_page_words (blank pages, covers, etc.)
    """

    def __init__(self, min_page_words: int = 10):
        self.min_page_words = min_page_words

    def process(self, filepath: str, doc_id: Optional[str] = None) -> DocumentContent:
        """
        Process a PDF file and return extracted page content.

        Args:
            filepath: Absolute path to the PDF file.
            doc_id:   Optional document identifier. Auto-generated from
                      filename if not provided.

        Returns:
            DocumentContent containing per-page text and word counts.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If no extractable text is found.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF not found: {filepath}")

        filename = os.path.basename(filepath)
        if doc_id is None:
            doc_id = self._make_doc_id(filename)

        pages: list[PageContent] = []

        with fitz.open(filepath) as pdf:
            total_pages = len(pdf)
            for idx in range(total_pages):
                page = pdf[idx]
                raw = page.get_text("text")
                cleaned = self._clean(raw)
                wc = len(cleaned.split())
                if wc < self.min_page_words:
                    continue
                pages.append(PageContent(
                    page_number=idx + 1,
                    text=cleaned,
                    word_count=wc,
                ))

        if not pages:
            raise ValueError(
                f"No extractable text found in {filename}. "
                f"The file may be a scanned PDF without OCR."
            )

        return DocumentContent(
            filename=filename,
            doc_id=doc_id,
            page_count=total_pages,
            pages=pages,
            total_words=sum(p.word_count for p in pages),
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Strip whitespace while preserving paragraph line breaks."""
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    @staticmethod
    def _make_doc_id(filename: str) -> str:
        """Generate a filesystem-safe doc_id from a filename."""
        name = os.path.splitext(filename)[0]
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        return safe.lower()[:64]
