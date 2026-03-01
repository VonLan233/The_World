import { useEffect } from 'react';
import { wsClient } from '@/api/websocket';
import { EventBus, GameEvents } from '@/game/EventBus';
import { useSimulationStore } from '@/stores/useSimulationStore';
import { useRelationshipStore } from '@/stores/useRelationshipStore';
import type { WSServerMessage } from '@shared/types/events';

/**
 * Manages WebSocket connection lifecycle for a world simulation.
 * Connects on mount, dispatches incoming messages to stores,
 * and disconnects on unmount.
 */
export function useWorldSocket(
  worldId: string | undefined,
  characterId: string | null,
) {
  const updateCharacterState = useSimulationStore((s) => s.updateCharacterState);
  const addEvent = useSimulationStore((s) => s.addEvent);
  const addDialogue = useSimulationStore((s) => s.addDialogue);
  const setClockState = useSimulationStore((s) => s.setClockState);

  useEffect(() => {
    if (!worldId) return;

    wsClient.connect(worldId);

    // Wait for connection to be ready (wsClient emits a synthetic 'pong' on open)
    const unsubPong = wsClient.on('pong', () => {
      wsClient.send({ type: 'join_world', worldId });
      if (characterId) {
        wsClient.send({ type: 'place_character', characterId, x: 100, y: 300 });
      }
    });

    const unsubAll = wsClient.on('*', (msg: WSServerMessage) => {
      switch (msg.type) {
        case 'character_update':
          updateCharacterState(msg.update);
          EventBus.emit(GameEvents.MOVE_CHARACTER, {
            id: msg.update.characterId,
            x: msg.update.position.x,
            y: msg.update.position.y,
          });
          break;
        case 'clock_update':
          setClockState(msg.clock);
          break;
        case 'simulation_event':
          addEvent(msg.event);
          if (msg.event.type === 'relationship_update' && msg.event.data) {
            const d = msg.event.data as Record<string, unknown>;
            useRelationshipStore.getState().updateRelationshipFromEvent({
              characterId: msg.event.characterId,
              targetId: d.targetId as string,
              targetName: d.targetName as string,
              friendshipScore: d.friendshipScore as number,
              relationshipType: (d.relationshipType as string) ?? 'acquaintance',
            });
          }
          break;
        case 'world_state':
          setClockState(msg.clock);
          for (const charState of msg.characters) {
            updateCharacterState(charState);
            EventBus.emit(GameEvents.ADD_CHARACTER, {
              id: charState.characterId,
              name: charState.currentActivity,
              x: charState.position.x,
              y: charState.position.y,
            });
          }
          break;
        case 'dialogue':
          addDialogue(msg.dialogue);
          EventBus.emit(GameEvents.SHOW_SPEECH_BUBBLE, {
            characterId: msg.dialogue.speakerId,
            text: msg.dialogue.dialogue,
          });
          break;
        case 'character_joined':
          break;
      }
    });

    // Listen for character clicks from Phaser
    const onCharClick = (data: { id: string }) => {
      // Dispatch via EventBus — WorldPage listens for this to update selectedCharId
      EventBus.emit('worldSocket:characterClicked', data);
    };
    EventBus.on(GameEvents.CHARACTER_CLICKED, onCharClick);

    return () => {
      unsubPong();
      unsubAll();
      EventBus.off(GameEvents.CHARACTER_CLICKED, onCharClick);
      wsClient.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [worldId, characterId, updateCharacterState, addEvent, addDialogue, setClockState]);
}
