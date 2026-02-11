import { forwardRef, useEffect, useLayoutEffect, useRef } from 'react';
import Phaser from 'phaser';
import { createGameConfig } from './config';
import { EventBus } from './EventBus';

export interface PhaserGameRef {
  game: Phaser.Game | null;
  scene: Phaser.Scene | null;
}

interface PhaserGameProps {
  /** Callback fired when the active scene changes */
  onSceneReady?: (scene: Phaser.Scene) => void;
}

/**
 * React component that hosts the Phaser game canvas.
 * Creates the game on mount, destroys on unmount.
 * Exposes the game instance and current scene via forwardRef.
 */
const PhaserGame = forwardRef<PhaserGameRef, PhaserGameProps>(function PhaserGame(
  { onSceneReady },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  useLayoutEffect(() => {
    if (!containerRef.current) return;

    // Prevent double creation in React StrictMode
    if (gameRef.current) return;

    const config = createGameConfig(containerRef.current);
    const game = new Phaser.Game(config);
    gameRef.current = game;

    if (typeof ref === 'function') {
      ref({ game, scene: null });
    } else if (ref) {
      ref.current = { game, scene: null };
    }

    return () => {
      if (gameRef.current) {
        gameRef.current.destroy(true);
        gameRef.current = null;
      }
    };
  }, [ref]);

  useEffect(() => {
    const handleSceneReady = (scene: Phaser.Scene) => {
      if (typeof ref === 'function') {
        ref({ game: gameRef.current, scene });
      } else if (ref) {
        ref.current = { game: gameRef.current, scene };
      }

      onSceneReady?.(scene);
    };

    EventBus.on('scene-ready', handleSceneReady);

    return () => {
      EventBus.off('scene-ready', handleSceneReady);
    };
  }, [ref, onSceneReady]);

  return (
    <div
      ref={containerRef}
      id="phaser-game-container"
      style={{
        width: '100%',
        height: '100%',
        minHeight: '400px',
      }}
    />
  );
});

export default PhaserGame;
