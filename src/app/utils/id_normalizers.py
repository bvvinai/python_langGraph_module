from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5


_UUID_NAMESPACE = NAMESPACE_URL


def stable_uuid(raw_id: str) -> UUID:
    return uuid5(_UUID_NAMESPACE, raw_id)
