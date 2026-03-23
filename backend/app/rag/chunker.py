"""
CampusGenie — Text Chunker
Splits extracted PDF pages into overlapping chunks for embedding.
Preserves source metadata (filename, page number) for citations.

Chunking strategy: word-based sliding window with configurable
overlap to preserve semantic continuity across chunk boundaries.
Default: chunk_size=500 words, chunk_overlap=50 words.
"""

from dataclasses import dataclass, field
from app.rag.pdf_processor import DocumentContent


@dataclass
class TextChunk:
    """A single chunk of text with full source metadata."""
    chunk_id: str           # unique: {doc_id}_p{page}_c{idx}
    doc_id: str
    filename: str
    page_number: int
    text: str
    char_count: int = field(init=False)

    def __post_init__(self):
        self.char_count = len(self.text)


class TextChunker:
    """
    Splits document pages into overlapping fixed-size chunks.

    Why chunking?
      LLMs and embedding models have token limits.
      Chunking + overlap ensures context is not lost at boundaries.

    Strategy:
      - Split by sentence boundaries where possible
      - Fall back to word-level splitting
      - Each chunk carries source page + doc metadata for citations
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size:    Target character count per chunk
            chunk_overlap: Characters shared between adjacent chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: DocumentContent) -> list[TextChunk]:
        """
        Chunk an entire DocumentContent object.

        Returns:
            List of TextChunk objects ready for embedding
        """
        all_chunks: list[TextChunk] = []

        for page in doc.pages:
            page_chunks = self._chunk_text(page.text)
            for idx, chunk_text in enumerate(page_chunks):
                chunk = TextChunk(
                    chunk_id=f"{doc.doc_id}_p{page.page_number}_c{idx}",
                    doc_id=doc.doc_id,
                    filename=doc.filename,
                    page_number=page.page_number,
                    text=chunk_text,
                )
                all_chunks.append(chunk)

        return all_chunks

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split a block of text into overlapping chunks.

        Uses a sliding window approach:
          1. Split text into words
          2. Accumulate words until chunk_size is reached
          3. Step back chunk_overlap chars for the next chunk
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at a sentence boundary (. ! ?)
            if end < len(text):
                boundary = self._find_sentence_boundary(text, start, end)
                if boundary:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move forward but keep overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    @staticmethod
    def _find_sentence_boundary(text: str, start: int, end: int) -> int | None:
        """
        Look backward from `end` within the last 100 chars for a sentence end.
        Returns the position after the punctuation, or None if not found.
        """
        search_start = max(start, end - 100)
        for i in range(end, search_start, -1):
            if text[i - 1] in ".!?":
                return i
        return None
