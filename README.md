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

- `type = "anthropic"` for Anthropic Messages API (`/v1/messages`).
- `type = "openai_compatible"` for OpenAI-style APIs (`/v1/chat/completions`) including many self-hosted or vendor gateways.
- `type = "ollama"` for local/self-hosted Ollama (`/api/chat`).

Config supports env placeholders like `${ANTHROPIC_BASE_URL}`, `${OPENAI_BASE_URL}`, and `${OLLAMA_BASE_URL}`.

To add a new AI system, usually you only need to:

1. Add a provider entry in `config/providers.json`.
2. Set required API key env var.
3. Optionally create a dedicated provider class if API is not OpenAI-compatible.

## Switch providers anytime

1. See available providers:

```bash
curl "http://127.0.0.1:8000/v1/ai/providers"
```

2. Call any provider per request by changing `provider`:

```bash
curl -X POST "http://127.0.0.1:8000/v1/ai/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain this in one sentence.",
    "provider": "anthropic"
  }'
```

```bash
curl -X POST "http://127.0.0.1:8000/v1/ai/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain this in one sentence.",
    "provider": "openai"
  }'
```

```bash
curl -X POST "http://127.0.0.1:8000/v1/ai/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain this in one sentence.",
    "provider": "ollama"
  }'
```

3. Change global default in `.env` via `DEFAULT_PROVIDER`.

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/v1/ai/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Summarize LangGraph in one line.",
    "system_prompt": "You are concise.",
    "provider": "openai"
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
