# config

Runtime JSON configuration files for providers and embeddings.

## Folder Flow Chart

```mermaid
flowchart TD
  S([Start]) --> A[providers.json]
  A --> B[app/providers/registry.py]
  B --> C[ProviderFactory]
  S --> D[embeddings.json]
  D --> E[app/vectordb/registry.py]
  E --> F[Vector store factory]
  C --> G[Runtime provider selection]
  F --> H[Runtime embedding selection]
  G --> Z([End])
  H --> Z
```

## Files

### providers.json
Provider catalog used by provider registry/factory.

No Python functions or classes.

### embeddings.json
Embedding profile catalog used by vector DB embedding registry.

No Python functions or classes.
