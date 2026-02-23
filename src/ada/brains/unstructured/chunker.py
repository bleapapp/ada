"""Document chunking for embedding pipeline."""

from __future__ import annotations

from pydantic import BaseModel


class Chunk(BaseModel):
    text: str
    metadata: dict[str, str] = {}
    index: int = 0


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    metadata: dict[str, str] | None = None,
) -> list[Chunk]:
    """Split text into overlapping chunks for embedding.

    Args:
        text: The source text to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.
        metadata: Metadata to attach to each chunk.

    Returns:
        List of Chunk objects.
    """
    if not text.strip():
        return []

    meta = metadata or {}
    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence boundary (only if not at the end)
        if end < len(text):
            for sep in [". ", ".\n", "!\n", "?\n", "\n\n"]:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break

        chunk_text_content = text[start:end].strip()
        if chunk_text_content:
            chunks.append(Chunk(text=chunk_text_content, metadata=meta, index=index))
            index += 1

        # If we've reached the end, stop
        if end >= len(text):
            break

        # Move forward, ensuring we always make progress
        next_start = end - chunk_overlap
        start = max(next_start, start + 1)

    return chunks
