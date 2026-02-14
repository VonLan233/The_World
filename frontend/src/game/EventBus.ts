import Phaser from 'phaser';

/**
 * Event bus for React <-> Phaser communication.
 * Uses Phaser's EventEmitter so both sides share the same event system.
 *
 * Usage from React:
 *   EventBus.emit('character-move', { id: '...', x: 100, y: 200 });
 *   EventBus.on('scene-ready', callback);
 *
 * Usage from Phaser scene:
 *   EventBus.on('character-move', handler, this);
 *   EventBus.emit('scene-ready', this);
 */
export const EventBus = new Phaser.Events.EventEmitter();

/** Well-known event names for type safety */
export const GameEvents = {
  /** Emitted by Phaser when a scene is fully ready */
  SCENE_READY: 'scene-ready',
  /** Emitted by React to request character placement */
  ADD_CHARACTER: 'add-character',
  /** Emitted by React to move a character sprite */
  MOVE_CHARACTER: 'move-character',
  /** Emitted by React to remove a character sprite */
  REMOVE_CHARACTER: 'remove-character',
  /** Emitted by Phaser when a character sprite is clicked */
  CHARACTER_CLICKED: 'character-clicked',
  /** Emitted by React to update the simulation clock display */
  CLOCK_UPDATE: 'clock-update',
  /** Emitted by React when a dialogue event arrives — shows a speech bubble */
  SHOW_SPEECH_BUBBLE: 'show-speech-bubble',
} as const;
