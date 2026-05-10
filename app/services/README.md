# app/services

Service layer for orchestration and runtime dependency wiring.

## Files

### __init__.py
Package initializer.

No top-level classes or functions.

### orchestrator.py
Orchestrator entrypoint for invoke operations.

#### Classes and Methods

- **AIOrchestrator**
  - `__init__(graph_runner: AIGraphRunner)`
    - Input: Graph runner instance.
    - Output: None
    - Doc: Stores graph runner dependency.
  - `async invoke(request: AIInvokeRequest) -> AIInvokeResponse`
    - Input: Invoke request.
    - Output: AI invoke response.
    - Doc: Creates trace ID and executes graph workflow.

### runtime.py
Dependency singleton providers used by FastAPI.

#### Functions

- **get_provider_factory() -> ProviderFactory**
  - Input: None
  - Output: Cached ProviderFactory singleton.
  - Doc: Loads provider registry and returns provider factory.

- **get_vector_store() -> VectorStore**
  - Input: None
  - Output: Cached VectorStore singleton.
  - Doc: Builds vector store from settings via VectorStoreFactory.

- **get_orchestrator() -> AIOrchestrator**
  - Input: None
  - Output: Cached AIOrchestrator singleton.
  - Doc: Wires provider factory and vector store into graph orchestrator.

