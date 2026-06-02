from __future__ import annotations

from pathlib import Path

from app.contracts.ingestion import BaseLoader, DocumentBlob, ParsedDocument


class TextLoader(BaseLoader):
    name = "text"
    _extensions = {".txt", ".md", ".rst", ".log"}

    def supports(self, filename: str, content_type: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in self._extensions or content_type.startswith("text/")

    async def load(self, blob: DocumentBlob) -> ParsedDocument:
        text = blob.content_bytes.decode("utf-8", errors="ignore")
        return ParsedDocument(
            document_id=blob.document_id,
            text=text,
            metadata={
                **blob.metadata,
                "filename": blob.filename,
                "loader": self.name,
            },
        )
