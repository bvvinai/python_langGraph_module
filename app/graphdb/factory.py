from __future__ import annotations

from app.core.config import Settings
from app.domain.ports import GraphStore
from app.graphdb.neo4j import Neo4jGraphStore


def build_graph_store(settings: Settings) -> GraphStore | None:
    if not settings.graph_db_enabled:
        return None

    if settings.graph_db_provider != "neo4j":
        return None

    return Neo4jGraphStore(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password_env=settings.neo4j_password_env,
        database=settings.neo4j_database,
        default_neighbors=settings.graph_rag_max_neighbors,
    )
