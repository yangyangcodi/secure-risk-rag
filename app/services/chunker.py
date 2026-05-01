"""
Chunker — splits long text into overlapping word-level chunks.

Why overlapping?
  If a sentence spans the boundary of two chunks, overlap ensures
  it appears fully in at least one chunk — so nothing gets cut off
  and lost during retrieval.
"""

from typing import List

CHUNK_SIZE = 512    # words per chunk
CHUNK_OVERLAP = 64  # words shared between consecutive chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping word-level chunks.

    Args:
        text:       The raw input text.
        chunk_size: Maximum number of words per chunk.
        overlap:    Number of words to repeat at the start of the next chunk.

    Returns:
        List of text chunks.
    """
    words = text.split()

    if not words:
        return []

    chunks: List[str] = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap

    return chunks
