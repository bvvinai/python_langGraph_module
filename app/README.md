# app

Application source code organized by API, domain, orchestration, providers, and vector DB modules.

## Subfolders

- api/
- core/
- domain/
- graphs/
- providers/
- services/
- vectordb/

## Files

### __init__.py
Package initializer.

No top-level classes or functions.

### main.py
Application bootstrap and FastAPI setup.

#### Functions and Handlers

- **create_app() -> FastAPI**
  - Input: None
  - Output: FastAPI app instance
  - Doc: Creates and configures the FastAPI app, logging, middleware, error handlers, and API router.

- **request_context_middleware(request: Request, call_next)**
  - Input: request (Request), call_next (callable)
  - Output: Response
  - Doc: Middleware to add trace ID to each request and log start and finish.

- **app_error_handler(_: Request, exc: AppError) -> JSONResponse**
  - Input: Request, AppError
  - Output: JSON error response (400)
  - Doc: Handles custom AppError exceptions.

- **unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse**
  - Input: Request, Exception
  - Output: JSON error response (500)
  - Doc: Handles all uncaught exceptions and logs the error.

