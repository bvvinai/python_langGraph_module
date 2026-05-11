from __future__ import annotations

from io import BytesIO
from pathlib import Path

from app.core.exceptions import AppError


def _extract_text_from_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    page_text: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            page_text.append(text)
    return "\n\n".join(page_text).strip()


def _extract_text_from_docx(content: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(content))
    lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(lines).strip()


def _extract_text_from_plain(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()


def extract_text_from_uploaded_file(*, filename: str | None, content: bytes) -> tuple[str, str]:
    suffix = Path(filename or "").suffix.lower()

    if suffix == ".pdf":
        text = _extract_text_from_pdf(content)
        parser = "pdf"
    elif suffix == ".docx":
        text = _extract_text_from_docx(content)
        parser = "docx"
    else:
        text = _extract_text_from_plain(content)
        parser = "plain"

    if not text:
        raise AppError(
            "Could not extract text from file. Supported types: .txt, .md, .docx, .pdf.",
            code="invalid_upload_file",
        )

    return text, parser
