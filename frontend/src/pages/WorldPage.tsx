import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import PhaserGame, { type PhaserGameRef } from '@/game/PhaserGame';
import { EventBus, GameEvents } from '@/game/EventBus';
import { wsClient } from '@/api/websocket';
import { useSimulationStore } from '@/stores/useSimulationStore';
import NeedsDisplay from '@/components/character/NeedsDisplay';
import type { CharacterNeeds } from '@shared/types/character';
import type { WSServerMessage } from '@shared/types/events';
import type { CharacterStateUpdate } from '@shared/types/simulation';
import styles from './WorldPage.module.css';

const SPEED_OPTIONS = [1, 2, 5];

/**
 * Main simulation page.
 * Contains the Phaser game canvas (center), character info sidebar (right),
 * and event log panel (bottom).
 */
export default function WorldPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const gameRef = useRef<PhaserGameRef>(null);
  const [speed, setSpeed] = useState(1);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);

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
    wsClient.send({ type: 'join_world', worldId });

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
        case 'character_joined':
          break;
      }
    });

    // Listen for character clicks from Phaser
    const onCharClick = (data: { id: string }) => {
      setSelectedCharId(data.id);
    };
    EventBus.on(GameEvents.CHARACTER_CLICKED, onCharClick);

    return () => {
      unsubAll();
      EventBus.off(GameEvents.CHARACTER_CLICKED, onCharClick);
      wsClient.disconnect();
    };
  }, [worldId, updateCharacterState, addEvent, setClockState]);

  const handleSceneReady = useCallback((_scene: Phaser.Scene) => {
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

  // Get selected or first character state for sidebar
  const selectedState: CharacterStateUpdate | undefined =
    (selectedCharId ? characterStates.get(selectedCharId) : undefined) ??
    characterStates.values().next().value;

  const displayNeeds: CharacterNeeds = selectedState?.needs ?? {
    hunger: 75, energy: 60, social: 45, fun: 80, hygiene: 90, comfort: 65,
  };

  const handleToggle = () => {
    toggleSimulation();
    wsClient.send({ type: 'toggle_simulation', running: !isRunning });
  };

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
    wsClient.send({ type: 'set_speed', speed: newSpeed });
  };

  const formatTime = (hour: number): string => {
    return `${String(hour).padStart(2, '0')}:00`;
  };

  const seasonIcon = (s: string): string => {
    switch (s) {
      case 'spring': return '\u{1F338}';
      case 'summer': return '\u{2600}\u{FE0F}';
      case 'autumn': return '\u{1F342}';
      case 'winter': return '\u{2744}\u{FE0F}';
      default: return '';
    }
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
          {/* Clock + Controls */}
          <div className={styles.sidebarSection}>
            <h3 className={styles.sidebarTitle}>Simulation</h3>
            <div className={styles.clockInfo}>
              <div className={styles.clockMain}>
                <span className={styles.clockTimeDisplay}>{formatTime(currentHour)}</span>
                <span className={styles.clockDayDisplay}>
                  Day {currentDay} {seasonIcon(currentSeason)} {currentSeason}
                </span>
              </div>
            </div>

            <div className={styles.controls}>
              <button
                className={`${styles.toggleBtn} ${isRunning ? styles.toggleRunning : ''}`}
                onClick={handleToggle}
              >
                {isRunning ? '\u23F8 Pause' : '\u25B6 Play'}
              </button>

              <div className={styles.speedControls}>
                {SPEED_OPTIONS.map((s) => (
                  <button
                    key={s}
                    className={`${styles.speedBtn} ${speed === s ? styles.speedActive : ''}`}
                    onClick={() => handleSpeedChange(s)}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Character Info */}
          <div className={styles.sidebarSection}>
            <h3 className={styles.sidebarTitle}>Character</h3>
            {selectedState ? (
              <div className={styles.charInfo}>
                <div className={styles.charInfoRow}>
                  <span className={styles.charInfoLabel}>Activity</span>
                  <span className={styles.charInfoValue}>{selectedState.currentActivity}</span>
                </div>
                <div className={styles.charInfoRow}>
                  <span className={styles.charInfoLabel}>Location</span>
                  <span className={styles.charInfoValue}>{selectedState.currentLocation}</span>
                </div>
                <div className={styles.charInfoRow}>
                  <span className={styles.charInfoLabel}>Mood</span>
                  <span className={styles.charInfoValue}>
                    {selectedState.mood} ({Math.round(selectedState.moodScore)})
                  </span>
                </div>
              </div>
            ) : (
              <p className={styles.placeholder}>
                No character in simulation. Add one to begin.
              </p>
            )}
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
                  T{event.tick}
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
