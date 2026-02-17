"""WebSocket endpoint for real-time simulation streaming."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from the_world.db.session import async_session_factory
from the_world.services.simulation_manager import SimulationManager

logger = logging.getLogger("the_world.ws")

router = APIRouter()


# ---------------------------------------------------------------------------
# Connection pool (per-world)
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Track WebSocket connections grouped by world_id."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, world_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(world_id, []).append(ws)

    def disconnect(self, world_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(world_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(world_id, None)

    async def broadcast(self, world_id: str, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(world_id, []):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(world_id, ws)

    def count(self, world_id: str) -> int:
        return len(self._connections.get(world_id, []))


# Module-level singleton
connection_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/{world_id}")
async def simulation_ws(websocket: WebSocket, world_id: str) -> None:
    """Real-time simulation WebSocket.

    Client messages (JSON): see ``shared/types/events.ts → WSClientMessage``
    Server messages (JSON): see ``shared/types/events.ts → WSServerMessage``
    """
    sim_manager: SimulationManager | None = getattr(
        websocket.app.state, "sim_manager", None
    )

    await connection_manager.connect(world_id, websocket)
    logger.info("WS client connected to world %s", world_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "join_world":
                # Send current state snapshot
                if sim_manager:
                    engine = sim_manager.get_engine(world_id)
                    if engine:
                        state = engine.get_state()
                        await websocket.send_json({
                            "type": "world_state",
                            "characters": state["characters"],
                            "clock": state["clock"],
                            "weather": state.get("weather", {}),
                        })

            elif msg_type == "toggle_simulation":
                if sim_manager:
                    engine = sim_manager.get_or_create_engine(world_id)
                    if msg.get("running"):
                        engine.start()
                    else:
                        engine.pause()
                    await connection_manager.broadcast(world_id, {
                        "type": "clock_update",
                        "clock": engine.clock.to_clock_state(),
                    })

            elif msg_type == "set_speed":
                speed = msg.get("speed", 1)
                if sim_manager:
                    engine = sim_manager.get_engine(world_id)
                    if engine:
                        engine.set_speed(float(speed))

            elif msg_type == "place_character":
                char_id = msg.get("characterId")
                if char_id and sim_manager:
                    engine = sim_manager.get_or_create_engine(world_id)
                    # For now use a placeholder name/personality — the full
                    # version will load from DB
                    if char_id not in engine.characters:
                        name = msg.get("characterName", "Character")
                        personality = msg.get("personality", {
                            "openness": 0.5,
                            "conscientiousness": 0.5,
                            "extraversion": 0.5,
                            "agreeableness": 0.5,
                            "neuroticism": 0.5,
                        })
                        engine.add_character(char_id, name, personality)
                        await connection_manager.broadcast(world_id, {
                            "type": "character_joined",
                            "characterId": char_id,
                            "characterName": name,
                        })

            elif msg_type == "leave_world":
                break

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(world_id, websocket)
        logger.info("WS client disconnected from world %s", world_id)


def register_engine_callbacks(world_id: str, engine: Any) -> None:
    """Wire up engine tick/event callbacks to broadcast via WebSocket."""

    async def on_tick(payload: dict[str, Any]) -> None:
        # Broadcast character updates + clock + weather to all connected clients
        characters = payload.get("characters", [])
        clock = payload.get("clock", {})
        weather = payload.get("weather", {})

        await connection_manager.broadcast(world_id, {
            "type": "clock_update",
            "clock": clock,
            "weather": weather,
        })
        for char_update in characters:
            await connection_manager.broadcast(world_id, {
                "type": "character_update",
                "update": char_update,
            })

    async def on_event(event: dict[str, Any]) -> None:
        event_type = event.get("type", "unknown")
        await connection_manager.broadcast(world_id, {
            "type": "simulation_event",
            "event": {
                "id": str(__import__("uuid").uuid4()),
                "type": event_type,
                "characterId": event.get("characterId", ""),
                "characterName": event.get("characterName", ""),
                "description": event.get("description", ""),
                "timestamp": __import__("time").time(),
                "tick": event.get("tick", 0),
                "data": event.get("data", {}),
            },
        })

        # Persist memory-worthy random/birthday/seasonal events
        data = event.get("data", {})
        if (
            event_type in ("random_event", "birthday_event", "seasonal_event")
            and data.get("memoryWorthy")
            and event.get("characterId")
        ):
            try:
                from the_world.ai.memory import MemoryManager

                async with async_session_factory() as session:
                    mm = MemoryManager(session)
                    await mm.create_memory(
                        character_id=event["characterId"],
                        memory_type="random_event",
                        content=event.get("description", ""),
                        sim_timestamp=event.get("tick", 0),
                        importance=data.get("memoryImportance", 0.5),
                        emotional_valence=data.get("memoryValence", 0.0),
                        context={
                            "eventId": data.get("eventId"),
                            "category": data.get("category"),
                            "title": data.get("title"),
                        },
                    )
                    await session.commit()
            except Exception:
                logger.exception("Failed to persist random event memory")

    # -- AI encounter callback --
    from the_world.ai.integration import AIIntegration

    ai_integration = AIIntegration(engine, async_session_factory)

    async def on_encounter(payload: dict[str, Any]) -> None:
        tick = payload.get("tick", 0)
        try:
            dialogue_events = await ai_integration.process_encounters(tick)
            for evt in dialogue_events:
                await connection_manager.broadcast(world_id, {
                    "type": "dialogue",
                    "dialogue": evt,
                })
        except Exception:
            logger.exception("Error processing AI encounters")

    engine.on_tick(on_tick)
    engine.on_event(on_event)
    engine.on_encounter(on_encounter)
