"""
Unit tests for the TextChunker module.
Run with: pytest backend/tests/
"""

import pytest
from app.rag.chunker import TextChunker
from app.rag.pdf_processor import DocumentContent, PageContent


def make_doc(text: str, page: int = 1) -> DocumentContent:
    words = text.split()
    return DocumentContent(
        filename="test.pdf",
        doc_id="test",
        page_count=1,
        pages=[PageContent(page_number=page, text=text, word_count=len(words))],
        total_words=len(words),
    )


def test_basic_chunking():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    doc = make_doc(" ".join([f"word{i}" for i in range(25)]))
    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    for c in chunks:
        assert c.doc_id == "test"
        assert c.page_number == 1
        assert len(c.text.split()) <= 10


def test_short_page_single_chunk():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    doc = make_doc("This is a very short page.")
    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0


def test_chunk_ids_are_unique():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    doc = make_doc(" ".join([f"w{i}" for i in range(50)]))
    chunks = chunker.chunk_document(doc)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs detected"


def test_overlap_creates_shared_words():
    chunker = TextChunker(chunk_size=5, chunk_overlap=2)
    words = [f"w{i}" for i in range(10)]
    doc = make_doc(" ".join(words))
    chunks = chunker.chunk_document(doc)
    if len(chunks) >= 2:
        c1_words = set(chunks[0].text.split())
        c2_words = set(chunks[1].text.split())
        overlap = c1_words & c2_words
        assert len(overlap) >= 1
