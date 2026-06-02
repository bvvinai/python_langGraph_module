from __future__ import annotations

from app.contracts.ingestion import BaseLoader, DocumentBlob

from .document_loader import DocumentLoader
from .email_loader import EmailLoader
from .structured_loader import StructuredLoader
from .text_loader import TextLoader


class LoaderRegistry:
    def __init__(self) -> None:
        self._loaders: list[BaseLoader] = [
            DocumentLoader(),
            EmailLoader(),
            StructuredLoader(),
            TextLoader(),
        ]

    def resolve(self, blob: DocumentBlob) -> BaseLoader:
        for loader in self._loaders:
            if loader.supports(blob.filename, blob.content_type):
                return loader
        return TextLoader()
