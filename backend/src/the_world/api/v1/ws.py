"""WebSocket placeholder for real-time simulation streaming."""

import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/{world_id}")
async def simulation_ws(websocket: WebSocket, world_id: uuid.UUID) -> None:
    """Placeholder WebSocket endpoint.

    Accepts a connection, sends a welcome message, then echoes any
    incoming messages back to the client.  This will be replaced by the
    real simulation event stream once the engine is wired up.
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "welcome",
        "world_id": str(world_id),
        "message": "Connected to The World simulation stream (placeholder).",
    })

    try:
        while True:
            data = await websocket.receive_text()
            # Echo the message back with a wrapper
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"raw": data}

            await websocket.send_json({
                "type": "echo",
                "world_id": str(world_id),
                "payload": payload,
            })
    except WebSocketDisconnect:
        pass
