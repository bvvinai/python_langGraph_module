# app/api/v1

Version 1 API router composition.

## Folder Flow Chart

```mermaid
flowchart TD
  S([Start]) --> A[api_router]
  A --> B[Include health router]
  A --> C[Include ai router]
  B --> D[GET /v1/health]
  C --> E[GET /v1/ai/providers]
  C --> F[POST /v1/ai/invoke]
  C --> G[POST /v1/ai/vector/upsert]
  C --> H[GET /v1/ai/vector/config]
  D --> Z([End])
  E --> Z
  F --> Z
  G --> Z
  H --> Z
```

## Subfolders

- endpoints/

## Files

### __init__.py
Package initializer.

No top-level classes or functions.

### router.py
Composes v1 endpoint routers.

#### Top-level Objects

- **api_router (APIRouter)**
  - Input: None
  - Output: APIRouter instance with health and ai routers included.
  - Doc: Root v1 API router composed from endpoint routers.

No top-level functions or classes.

