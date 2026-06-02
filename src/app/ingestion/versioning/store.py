from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any


@dataclass(slots=True)
class DocumentVersion:
    document_id: str
    version_id: str
    source_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stats: dict[str, Any] = field(default_factory=dict)


class VersionStore:
    def __init__(self) -> None:
        self._versions: dict[str, list[DocumentVersion]] = {}

    @staticmethod
    def compute_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def add_version(self, document_id: str, content: bytes, stats: dict[str, Any]) -> DocumentVersion:
        source_hash = self.compute_hash(content)
        version_id = f"{document_id}:{source_hash[:12]}"
        version = DocumentVersion(
            document_id=document_id,
            version_id=version_id,
            source_hash=source_hash,
            stats=stats,
        )
        self._versions.setdefault(document_id, []).append(version)
        return version

    def get_versions(self, document_id: str) -> list[DocumentVersion]:
        return list(self._versions.get(document_id, []))
