# LangGraph + FastAPI Production Starter

A provider-agnostic, production-structured Python template that lets you plug in almost any AI backend with minimal changes.

## Why this template

- Provider-agnostic architecture via a strict provider port (`LLMProvider`) and registry config.
- LangGraph orchestration with clear node boundaries.
- FastAPI API layer separated from orchestration and provider implementations.
- Designed for extension: new providers, new graph nodes, new endpoints.

## Quick start

1. Create virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

2. Copy and edit environment variables:

```bash
copy .env.example .env
```

3. Run API:

```bash
uvicorn app.main:app --reload
```

4. Open docs:

- `http://127.0.0.1:8000/docs`

## Provider setup

Provider definitions are in `config/providers.json`.

- `type = "mock"` for local deterministic responses.
- `type = "openai_compatible"` for OpenAI-style APIs (`/v1/chat/completions`) including many self-hosted or vendor gateways.

To add a new AI system, usually you only need to:

1. Add a provider entry in `config/providers.json`.
2. Set required API key env var.
3. Optionally create a dedicated provider class if API is not OpenAI-compatible.

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/v1/ai/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Summarize LangGraph in one line.",
    "system_prompt": "You are concise.",
    "provider": "mock"
  }'
```

## Project structure

```text
app/
  api/
  core/
  domain/
  graphs/
  providers/
  services/
config/
  providers.json
tests/
```

## Production notes

- Wire your preferred authN/authZ middleware in `app/main.py`.
- Add tracing/metrics backend in observability middleware.
- Run behind a production ASGI server setup (gunicorn+uvicorn workers or orchestrator-managed replicas).
- Add CI for lint, type-check, tests.
