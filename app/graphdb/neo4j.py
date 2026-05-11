from __future__ import annotations

import os
import re
from collections import Counter

from app.domain.ports import GraphEdge, GraphNeighborhood, VectorDocument


def _extract_entities(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{2,}\b", text)
    if not candidates:
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_\-]{3,}\b", text)
        common = Counter(token.lower() for token in tokens)
        return [token for token, _ in common.most_common(5)]
    unique = []
    for entity in candidates:
        if entity not in unique:
            unique.append(entity)
    return unique[:10]


def _extract_edges(text: str, entities: list[str]) -> list[GraphEdge]:
    if len(entities) < 2:
        return []

    relation = "related_to"
    if "uses" in text.lower():
        relation = "uses"
    elif "depends on" in text.lower():
        relation = "depends_on"

    edges: list[GraphEdge] = []
    for idx in range(len(entities) - 1):
        source = entities[idx]
        target = entities[idx + 1]
        edges.append(GraphEdge(source=source, relation=relation, target=target, weight=1.0))
    return edges


class Neo4jGraphStore:
    def __init__(
        self,
        *,
        uri: str,
        username: str,
        password_env: str | None,
        database: str,
        default_neighbors: int,
    ) -> None:
        self.uri = uri
        self.username = username
        self.password = os.getenv(password_env, "") if password_env else ""
        self.database = database
        self.default_neighbors = default_neighbors

        try:
            from neo4j import GraphDatabase
        except Exception:
            self._driver = None
            return

        self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    async def upsert_documents(self, *, collection: str, documents: list[VectorDocument]) -> int:
        if self._driver is None:
            return 0

        total_edges = 0
        for doc in documents:
            entities = _extract_entities(doc.text)
            edges = _extract_edges(doc.text, entities)
            if not entities:
                continue
            total_edges += len(edges)
            with self._driver.session(database=self.database) as session:
                for entity in entities:
                    session.run(
                        """
                        MERGE (e:Entity {name: $name, collection: $collection})
                        """,
                        name=entity,
                        collection=collection,
                    )

                for edge in edges:
                    session.run(
                        """
                        MERGE (s:Entity {name: $source, collection: $collection})
                        MERGE (t:Entity {name: $target, collection: $collection})
                        MERGE (s)-[r:RELATED_TO {type: $relation}]->(t)
                        SET r.weight = coalesce(r.weight, 0) + $weight
                        """,
                        source=edge.source,
                        target=edge.target,
                        relation=edge.relation,
                        weight=edge.weight,
                        collection=collection,
                    )
        return total_edges

    async def query_neighborhood(self, *, collection: str, query: str, limit: int) -> GraphNeighborhood:
        if self._driver is None:
            return GraphNeighborhood()

        entities = _extract_entities(query)
        if not entities:
            return GraphNeighborhood()

        neighbors = max(1, min(limit, self.default_neighbors))
        facts: list[str] = []
        edges: list[GraphEdge] = []

        with self._driver.session(database=self.database) as session:
            for entity in entities:
                result = session.run(
                    """
                    MATCH (s:Entity {name: $entity, collection: $collection})-[r:RELATED_TO]->(t:Entity {collection: $collection})
                    RETURN s.name AS source, r.type AS relation, t.name AS target, r.weight AS weight
                    ORDER BY r.weight DESC
                    LIMIT $limit
                    """,
                    entity=entity,
                    collection=collection,
                    limit=neighbors,
                )
                for row in result:
                    source = str(row.get("source", ""))
                    relation = str(row.get("relation", "related_to"))
                    target = str(row.get("target", ""))
                    weight = float(row.get("weight", 1.0))
                    edges.append(GraphEdge(source=source, relation=relation, target=target, weight=weight))
                    facts.append(f"{source} {relation} {target}")

        return GraphNeighborhood(entities=entities, edges=edges, facts=facts)
