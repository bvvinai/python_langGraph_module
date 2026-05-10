# tests

Automated tests for API behavior, provider wiring, and vector DB integration.

## Files

### test_health.py
Health endpoint tests.

#### Functions

- **test_health_endpoint() -> None**
  - Input: None (builds app/test client internally)
  - Output: None (assert-based test)
  - Doc: Verifies `/v1/health` returns 200 and expected keys.

### test_invoke.py
Invoke endpoint error behavior tests.

#### Functions

- **test_invoke_with_unknown_provider_returns_400() -> None**
  - Input: None
  - Output: None
  - Doc: Verifies unknown provider returns 400 with `provider_not_found`.

### test_providers.py
Provider listing endpoint tests.

#### Functions

- **test_list_providers() -> None**
  - Input: None
  - Output: None
  - Doc: Verifies `/v1/ai/providers` returns default and expected providers.

### test_embedding_factory.py
Embedding profile/factory selection tests.

#### Classes and Functions

- **FakeSettings**
  - Input fields: in-memory settings attributes for vector DB and embeddings.
  - Output: Test settings object used by VectorStoreFactory.

- **_write_embeddings_config(path: Path) -> None**
  - Input: Path for temp embeddings JSON.
  - Output: None (writes file).
  - Doc: Writes fixture embedding profiles used by tests.

- **test_factory_uses_hash_embedding_by_default(tmp_path: Path) -> None**
  - Input: `tmp_path` pytest fixture.
  - Output: None.
  - Doc: Verifies default profile creates HashEmbeddingModel.

- **test_factory_can_use_openai_compatible_embedding(tmp_path: Path) -> None**
  - Input: `tmp_path` pytest fixture.
  - Output: None.
  - Doc: Verifies profile switch creates OpenAICompatibleEmbeddingModel.

- **test_factory_can_use_ollama_embedding(tmp_path: Path) -> None**
  - Input: `tmp_path` pytest fixture.
  - Output: None.
  - Doc: Verifies profile switch creates OllamaEmbeddingModel.

### test_vector_integration.py
Vector retrieval and endpoint integration tests.

#### Classes and Functions

- **FakeProvider**
  - `async generate(user_input, system_prompt, model, temperature, max_tokens, metadata) -> ProviderOutput`
  - Input: Provider generate args.
  - Output: Echo-like ProviderOutput.
  - Doc: Test provider used to isolate graph behavior.

- **FakeProviderFactory**
  - `__init__() -> None`
    - Input: None
    - Output: None
    - Doc: Sets default provider to `fake`.
  - `get(name: str | None = None) -> FakeProvider`
    - Input: Optional provider name.
    - Output: FakeProvider instance.
    - Doc: Returns fake provider for tests.

- **FakeVectorStore(VectorStore)**
  - `async upsert_documents(collection: str, documents: list[VectorDocument]) -> int`
    - Input: Collection and documents.
    - Output: Number of docs.
    - Doc: Simulates successful upsert.
  - `async search(collection: str, query: str, limit: int, score_threshold: float | None) -> list[RetrievedChunk]`
    - Input: Search args.
    - Output: One static RetrievedChunk.
    - Doc: Simulates retrieval results.

- **test_graph_runner_uses_retrieval_context() -> None**
  - Input: None
  - Output: None
  - Doc: Verifies graph uses retrieved context in generated output.

- **test_vector_upsert_endpoint() -> None**
  - Input: None
  - Output: None
  - Doc: Verifies vector upsert endpoint returns expected collection and count.

- **test_vector_runtime_config_endpoint() -> None**
  - Input: None
  - Output: None
  - Doc: Verifies runtime config endpoint includes vector and embedding keys.

