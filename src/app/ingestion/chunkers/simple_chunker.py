from __future__ import annotations

from app.contracts.ingestion import BaseChunker, Chunk, ParsedDocument
from app.utils.id_normalizers import stable_uuid


class SlidingWindowChunker(BaseChunker):
    name = "sliding_window"

    def chunk(self, parsed: ParsedDocument, chunk_size: int, overlap: int) -> list[Chunk]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if overlap >= chunk_size:
            overlap = chunk_size // 5

        text = parsed.text or ""
        step = max(1, chunk_size - overlap)
        chunks: list[Chunk] = []
        for index, start in enumerate(range(0, len(text), step)):
            snippet = text[start : start + chunk_size].strip()
            if not snippet:
                continue
            chunk_id = str(stable_uuid(f"{parsed.document_id}:{index}:{snippet[:64]}"))
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=parsed.document_id,
                    index=index,
                    text=snippet,
                    metadata=dict(parsed.metadata),
                )
            )
        return chunks
