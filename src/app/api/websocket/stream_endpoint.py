from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_container
from app.contracts.streaming import StreamEvent

router = APIRouter(tags=["stream"])


@router.websocket("/v1/stream")
async def stream_endpoint(websocket: WebSocket) -> None:
    container = get_container()
    if not container.settings.enable_websocket:
        await websocket.close(code=1008, reason="WebSocket transport disabled")
        return

    await websocket.accept()
    session_id = str(uuid4())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"query": raw}

            event_type = payload.get("event_type", "input")
            if event_type == "cancel":
                event = StreamEvent(
                    event_type="complete",
                    session_id=session_id,
                    payload={"reason": "cancelled_by_client"},
                )
                await websocket.send_json(event.__dict__)
                continue

            query = payload.get("query", "").strip()
            if not query:
                event = StreamEvent(
                    event_type="error",
                    session_id=session_id,
                    payload={"message": "Missing query"},
                )
                await websocket.send_json(event.__dict__)
                continue

            if "vector_store" in payload:
                event = StreamEvent(
                    event_type="error",
                    session_id=session_id,
                    payload={
                        "message": "vector_store override is not supported. Configure DEFAULT_VECTOR_STORE in server settings.",
                    },
                )
                await websocket.send_json(event.__dict__)
                continue

            if "agent" in payload:
                event = StreamEvent(
                    event_type="error",
                    session_id=session_id,
                    payload={
                        "message": "agent routing is not supported. Use provider or default provider configuration.",
                    },
                )
                await websocket.send_json(event.__dict__)
                continue

            request = {
                "query": query,
                "mode": payload.get("mode", "agent"),
                "provider": payload.get("provider"),
                "model": payload.get("model"),
                "vector_enabled": payload.get("vector_enabled", True),
                "graph_enabled": payload.get("graph_enabled", True),
                "metadata": payload.get("metadata", {}),
            }

            await websocket.send_json(
                StreamEvent(
                    event_type="input",
                    session_id=session_id,
                    payload={"accepted": True},
                ).__dict__
            )

            collected = []
            async for token in container.graph_runtime.stream(request):
                collected.append(token)
                await websocket.send_json(
                    StreamEvent(
                        event_type="partial",
                        session_id=session_id,
                        payload={"token": token},
                    ).__dict__
                )

            await websocket.send_json(
                StreamEvent(
                    event_type="output",
                    session_id=session_id,
                    payload={"text": "".join(collected)},
                ).__dict__
            )
            await websocket.send_json(
                StreamEvent(
                    event_type="complete",
                    session_id=session_id,
                    payload={"done": True},
                ).__dict__
            )
    except WebSocketDisconnect:
        return
