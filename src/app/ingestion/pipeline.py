from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.contracts.ingestion import DocumentBlob, IngestionJob
from app.contracts.providers import EmbeddingRequest
from app.config.settings import Settings
from app.ingestion.chunkers.simple_chunker import SlidingWindowChunker
from app.ingestion.loaders.registry import LoaderRegistry
from app.ingestion.versioning.store import VersionStore
from app.router.embedding_router import EmbeddingRouter
from app.services.provider_manager import ProviderManager


class IngestionPipeline:
    def __init__(
        self,
        settings: Settings,
        providers: ProviderManager,
        embedding_router: EmbeddingRouter,
        version_store: VersionStore,
    ) -> None:
        self._settings = settings
        self._providers = providers
        self._embedding_router = embedding_router
        self._version_store = version_store
        self._loader_registry = LoaderRegistry()
        self._chunker = SlidingWindowChunker()
        self._jobs: dict[str, IngestionJob] = {}

    def get_job(self, job_id: str) -> IngestionJob | None:
        return self._jobs.get(job_id)

    async def ingest_blob(
        self,
        blob: DocumentBlob,
        collection: str | None = None,
        embedding_provider: str | None = None,
        graph_enabled: bool = True,
    ) -> IngestionJob:
        job = IngestionJob(
            job_id=str(uuid4()),
            document_id=blob.document_id,
            status="queued",
            message="Queued for ingestion",
        )
        self._jobs[job.job_id] = job
        self._touch(job, "in_progress", "Loading document")

        try:
            loader = self._loader_registry.resolve(blob)
            parsed = await loader.load(blob)
            self._touch(job, "in_progress", "Chunking document")

            chunks = self._chunker.chunk(
                parsed,
                chunk_size=self._settings.default_chunk_size,
                overlap=self._settings.default_chunk_overlap,
            )
            stats = {
                "loader": loader.name,
                "chunk_count": len(chunks),
                "content_chars": len(parsed.text),
            }
            version = self._version_store.add_version(blob.document_id, blob.content_bytes, stats)
            stats["version_id"] = version.version_id
            self._touch(job, "in_progress", "Document parsed and chunked", stats)

            if self._settings.enable_vectordb and chunks:
                await self._store_vectors(
                    blob,
                    chunks,
                    collection,
                    embedding_provider,
                )
                self._touch(job, "in_progress", "Embeddings stored", stats)

            if self._settings.enable_graphdb and graph_enabled and chunks:
                await self._store_graph(blob.document_id, chunks)
                self._touch(job, "in_progress", "Graph entities stored", stats)

            self._touch(job, "completed", "Ingestion completed", stats)
            return job
        except Exception as exc:  # noqa: BLE001
            self._touch(job, "failed", str(exc))
            return job

    async def _store_vectors(
        self,
        blob: DocumentBlob,
        chunks,
        collection: str | None,
        embedding_provider: str | None,
    ) -> None:
        provider_name = self._embedding_router.route(collection, embedding_provider)
        embedder = self._providers.get_embedding(provider_name)
        response = await embedder.embed(
            EmbeddingRequest(texts=[chunk.text for chunk in chunks], model=None)
        )
        store = self._providers.get_vector_store()
        await store.upsert(
            collection=collection or self._settings.default_vector_collection,
            ids=[chunk.chunk_id for chunk in chunks],
            vectors=response.vectors,
            payloads=[
                {
                    "document_id": blob.document_id,
                    "chunk_index": chunk.index,
                    "filename": blob.filename,
                    **chunk.metadata,
                }
                for chunk in chunks
            ],
        )

    async def _store_graph(self, document_id: str, chunks) -> None:
        entities: list[dict[str, str]] = []
        known_entities: set[str] = set()

        for chunk in chunks:
            words = chunk.text.split()
            for raw_word in words:
                word = raw_word.strip(".,;:()[]{}\"'")
                if len(word) < 3:
                    continue
                if not word[:1].isupper():
                    continue
                normalized = word.lower()
                if normalized in known_entities:
                    continue
                known_entities.add(normalized)
                entities.append(
                    {
                        "id": f"{document_id}:{normalized}",
                        "value": word,
                        "type": "concept",
                    }
                )

        relationships: list[dict[str, str]] = []
        graph_store = self._providers.get_graph_store("neo4j")
        await graph_store.upsert_entities(document_id, entities, relationships)

    @staticmethod
    def _touch(
        job: IngestionJob,
        status: str,
        message: str,
        stats: dict[str, object] | None = None,
    ) -> None:
        job.status = status
        job.message = message
        job.updated_at = datetime.now(timezone.utc)
        if stats:
            job.stats.update(stats)
