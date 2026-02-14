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

/** AI-generated dialogue event */
export interface DialogueEvent {
  id: string;
  speakerName: string;
  speakerId: string;
  targetName: string;
  targetId: string;
  dialogue: string;
  tierUsed: 'tier1_claude' | 'tier2_ollama' | 'tier3_rules';
  tick: number;
  timestamp: number;
  location: string;
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

/** Data payload for relationship_update events */
export interface RelationshipUpdateData {
  targetId: string;
  targetName: string;
  milestone: string;
  friendshipScore: number;
}
