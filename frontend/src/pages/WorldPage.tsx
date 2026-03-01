import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import PhaserGame, { type PhaserGameRef } from '@/game/PhaserGame';
import { EventBus, GameEvents } from '@/game/EventBus';
import { wsClient } from '@/api/websocket';
import { useSimulationStore } from '@/stores/useSimulationStore';
import { useWorldSocket } from '@/hooks/useWorldSocket';
import NeedsDisplay from '@/components/character/NeedsDisplay';
import RelationshipPanel from '@/components/relationship/RelationshipPanel';
import SimulationControls from '@/components/simulation/SimulationControls';
import SimulationEventLog from '@/components/simulation/SimulationEventLog';
import type { CharacterNeeds } from '@shared/types/character';
import type { CharacterStateUpdate } from '@shared/types/simulation';
import styles from './WorldPage.module.css';

/**
 * Main simulation page.
 * Contains the Phaser game canvas (center), character info sidebar (right),
 * and event log panel (bottom).
 */
export default function WorldPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const location = useLocation();
  const characterId = (location.state as { characterId?: string } | null)?.characterId ?? null;
  const gameRef = useRef<PhaserGameRef>(null);
  const [speed, setSpeed] = useState(1);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);

  useWorldSocket(worldId, characterId);

  const {
    isRunning,
    currentHour,
    currentDay,
    currentSeason,
    events,
    dialogues,
    characterStates,
    toggleSimulation,
  } = useSimulationStore();

  // Listen for character clicks relayed from useWorldSocket
  useEffect(() => {
    const onCharClick = (data: { id: string }) => {
      setSelectedCharId(data.id);
    };
    EventBus.on('worldSocket:characterClicked', onCharClick);
    EventBus.on(GameEvents.CHARACTER_CLICKED, onCharClick);
    return () => {
      EventBus.off('worldSocket:characterClicked', onCharClick);
      EventBus.off(GameEvents.CHARACTER_CLICKED, onCharClick);
    };
  }, []);

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

  return (
    <div className={styles.page}>
      <div className={styles.main}>
        <div className={styles.gameArea}>
          <PhaserGame ref={gameRef} onSceneReady={handleSceneReady} />
        </div>

        <aside className={styles.sidebar}>
          <SimulationControls
            isRunning={isRunning}
            currentHour={currentHour}
            currentDay={currentDay}
            currentSeason={currentSeason}
            speed={speed}
            onToggle={handleToggle}
            onSpeedChange={handleSpeedChange}
          />

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

          {/* Relationships */}
          <div className={styles.sidebarSection}>
            <RelationshipPanel characterId={selectedState?.characterId ?? null} />
          </div>
        </aside>
      </div>

      <SimulationEventLog events={events} dialogues={dialogues} />
    </div>
  );
}
