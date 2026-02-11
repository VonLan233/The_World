import { useCallback, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import PhaserGame, { type PhaserGameRef } from '@/game/PhaserGame';
import { EventBus, GameEvents } from '@/game/EventBus';
import { wsClient } from '@/api/websocket';
import { useSimulationStore } from '@/stores/useSimulationStore';
import NeedsDisplay from '@/components/character/NeedsDisplay';
import type { CharacterNeeds } from '@shared/types/character';
import type { WSServerMessage } from '@shared/types/events';
import styles from './WorldPage.module.css';

/**
 * Main simulation page.
 * Contains the Phaser game canvas (center), character info sidebar (right),
 * and event log panel (bottom).
 */
export default function WorldPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const gameRef = useRef<PhaserGameRef>(null);

  const {
    isRunning,
    currentHour,
    currentDay,
    currentSeason,
    events,
    characterStates,
    updateCharacterState,
    addEvent,
    setClockState,
    toggleSimulation,
  } = useSimulationStore();

  // Connect WebSocket on mount
  useEffect(() => {
    if (!worldId) return;

    wsClient.connect(worldId);

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
      }
    });

    return () => {
      unsubAll();
      wsClient.disconnect();
    };
  }, [worldId, updateCharacterState, addEvent, setClockState]);

  const handleSceneReady = useCallback((_scene: Phaser.Scene) => {
    // Scene is ready; add any initial characters from store
    const states = useSimulationStore.getState().characterStates;
    states.forEach((state, id) => {
      EventBus.emit(GameEvents.ADD_CHARACTER, {
        id,
        name: state.currentActivity,
        x: state.position.x,
        y: state.position.y,
      });
    });
  }, []);

  // Get first character state for sidebar display
  const firstCharState = characterStates.values().next().value;
  const displayNeeds: CharacterNeeds = firstCharState?.needs ?? {
    hunger: 75,
    energy: 60,
    social: 45,
    fun: 80,
    hygiene: 90,
    comfort: 65,
  };

  const handleToggle = () => {
    toggleSimulation();
    wsClient.send({ type: 'toggle_simulation', running: !isRunning });
  };

  return (
    <div className={styles.page}>
      {/* Main content area */}
      <div className={styles.main}>
        {/* Phaser canvas */}
        <div className={styles.gameArea}>
          <PhaserGame ref={gameRef} onSceneReady={handleSceneReady} />
        </div>

        {/* Sidebar */}
        <aside className={styles.sidebar}>
          <div className={styles.sidebarSection}>
            <h3 className={styles.sidebarTitle}>Simulation</h3>
            <div className={styles.clockInfo}>
              <div className={styles.clockRow}>
                <span className={styles.clockLabel}>Day</span>
                <span className={styles.clockValue}>{currentDay}</span>
              </div>
              <div className={styles.clockRow}>
                <span className={styles.clockLabel}>Hour</span>
                <span className={styles.clockValue}>
                  {String(currentHour).padStart(2, '0')}:00
                </span>
              </div>
              <div className={styles.clockRow}>
                <span className={styles.clockLabel}>Season</span>
                <span className={styles.clockValue}>
                  {currentSeason.charAt(0).toUpperCase() + currentSeason.slice(1)}
                </span>
              </div>
            </div>
            <button
              className={`${styles.toggleBtn} ${isRunning ? styles.toggleRunning : ''}`}
              onClick={handleToggle}
            >
              {isRunning ? 'Pause Simulation' : 'Start Simulation'}
            </button>
          </div>

          <div className={styles.sidebarSection}>
            <h3 className={styles.sidebarTitle}>Character Info</h3>
            <p className={styles.placeholder}>
              Select a character in the world to view details.
            </p>
            <NeedsDisplay needs={displayNeeds} />
          </div>
        </aside>
      </div>

      {/* Event log */}
      <div className={styles.eventLog}>
        <h4 className={styles.eventLogTitle}>Event Log</h4>
        <div className={styles.eventList}>
          {events.length === 0 ? (
            <p className={styles.eventEmpty}>
              No events yet. Start the simulation to see activity.
            </p>
          ) : (
            events.slice(0, 50).map((event) => (
              <div key={event.id} className={styles.eventItem}>
                <span className={styles.eventTime}>
                  Day {event.tick} &middot;
                </span>
                <span className={styles.eventChar}>{event.characterName}</span>
                <span className={styles.eventDesc}>{event.description}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
