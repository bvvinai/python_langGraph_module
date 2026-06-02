from __future__ import annotations

import asyncio
from email import policy
from email.parser import BytesParser
import os
from pathlib import Path
import tempfile

from app.contracts.ingestion import BaseLoader, DocumentBlob, ParsedDocument


def _parse_eml(content: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(content)
    lines = [
        f"Subject: {msg.get('subject', '')}",
        f"From: {msg.get('from', '')}",
        f"To: {msg.get('to', '')}",
    ]
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                lines.append(part.get_content())
    else:
        lines.append(msg.get_content())
    return "\n".join(line for line in lines if line)


def _parse_msg(content: bytes) -> str:
    try:
        import extract_msg
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("extract-msg is required for .msg files") from exc

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".msg", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        message = extract_msg.Message(tmp_path)
        return "\n".join(
            [
                f"Subject: {message.subject or ''}",
                f"From: {message.sender or ''}",
                f"To: {message.to or ''}",
                message.body or "",
            ]
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


class EmailLoader(BaseLoader):
    name = "email"
    _extensions = {".eml", ".msg"}

    def supports(self, filename: str, content_type: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in self._extensions or content_type in {
            "message/rfc822",
            "application/vnd.ms-outlook",
        }

    async def load(self, blob: DocumentBlob) -> ParsedDocument:
        ext = Path(blob.filename).suffix.lower()
        if ext == ".eml":
            text = await asyncio.to_thread(_parse_eml, blob.content_bytes)
        elif ext == ".msg":
            text = await asyncio.to_thread(_parse_msg, blob.content_bytes)
        else:
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
