from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase

from app.contracts.providers import BaseGraphStore
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


class Neo4jGraphStore(BaseGraphStore):
    name = "neo4j"

    def __init__(self, settings: Settings) -> None:
        user = settings.neo4j_user.strip()
        password = settings.neo4j_password.strip() if isinstance(settings.neo4j_password, str) else None

        if user and not password:
            raise ProviderConfigurationError(
                self.name,
                (
                    "Missing NEO4J_PASSWORD while NEO4J_USER is set. "
                    "Set NEO4J_PASSWORD (or disable graphdb with ENABLE_GRAPHDB=false)"
                ),
            )

        if password and not user:
            raise ProviderConfigurationError(
                self.name,
                "Missing NEO4J_USER while NEO4J_PASSWORD is set",
            )

        auth = (user, password) if user and password else None
        self._driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=auth)
        self._database = settings.neo4j_database

    async def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher, params or {})
            return [record.data() async for record in result]

    async def upsert_entities(
        self,
        document_id: str,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
    ) -> None:
        async with self._driver.session(database=self._database) as session:
            for entity in entities:
                await session.run(
                    """
                    MERGE (e:Entity {id: $id})
                    SET e += $props
                    WITH e
                    MERGE (d:Document {id: $document_id})
                    MERGE (d)-[:HAS_ENTITY]->(e)
                    """,
                    {
                        "id": entity["id"],
                        "props": entity,
                        "document_id": document_id,
                    },
                )
            for rel in relationships:
                await session.run(
                    """
                    MATCH (a:Entity {id: $source})
                    MATCH (b:Entity {id: $target})
                    MERGE (a)-[r:RELATED {type: $type}]->(b)
                    SET r += $props
                    """,
                    {
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel.get("type", "related"),
                        "props": rel,
                    },
                )

    async def close(self) -> None:
        await self._driver.close()
