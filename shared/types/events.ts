/**
 * WebSocket message types for real-time communication.
 * Uses a discriminated union pattern on the `type` field.
 */

import type { CharacterStateUpdate, ClockState, SimulationEvent } from './simulation';

/** Client -> Server messages */
export type WSClientMessage =
  | { type: 'join_world'; worldId: string }
  | { type: 'leave_world'; worldId: string }
  | { type: 'toggle_simulation'; running: boolean }
  | { type: 'set_speed'; speed: number }
  | { type: 'place_character'; characterId: string; x: number; y: number }
  | { type: 'ping' };

/** Server -> Client messages */
export type WSServerMessage =
  | { type: 'world_state'; characters: CharacterStateUpdate[]; clock: ClockState }
  | { type: 'character_update'; update: CharacterStateUpdate }
  | { type: 'clock_update'; clock: ClockState }
  | { type: 'simulation_event'; event: SimulationEvent }
  | { type: 'character_joined'; characterId: string; characterName: string }
  | { type: 'character_left'; characterId: string }
  | { type: 'error'; message: string; code?: string }
  | { type: 'pong' };

/** Combined WS message type */
export type WSMessage = WSClientMessage | WSServerMessage;
