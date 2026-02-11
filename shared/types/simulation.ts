/**
 * Simulation-related type definitions for The World.
 */

import type { CharacterNeeds } from './character';

/** Simulation clock state */
export interface ClockState {
  currentTick: number;
  currentHour: number;
  currentDay: number;
  currentSeason: 'spring' | 'summer' | 'autumn' | 'winter';
  isPaused: boolean;
}

/** Simulation event types */
export type SimulationEventType =
  | 'activity_start'
  | 'activity_end'
  | 'social_interaction'
  | 'need_critical'
  | 'mood_change'
  | 'location_change'
  | 'random_event'
  | 'relationship_update';

/** A single simulation event */
export interface SimulationEvent {
  id: string;
  type: SimulationEventType;
  characterId: string;
  characterName: string;
  description: string;
  timestamp: number;
  tick: number;
  data: Record<string, unknown>;
}

/** Character state update from the simulation engine */
export interface CharacterStateUpdate {
  characterId: string;
  needs: CharacterNeeds;
  currentActivity: string;
  currentLocation: string;
  mood: string;
  moodScore: number;
  position: { x: number; y: number };
}
