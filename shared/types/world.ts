/**
 * World and location type definitions for The World.
 */

/** A location within a world */
export interface Location {
  id: string;
  worldId: string;
  name: string;
  description: string;
  type: LocationType;
  position: { x: number; y: number };
  size: { width: number; height: number };
  capacity: number;
  currentOccupants: string[];
  properties: Record<string, unknown>;
}

/** Location categories */
export type LocationType =
  | 'home'
  | 'workplace'
  | 'park'
  | 'restaurant'
  | 'shop'
  | 'gym'
  | 'library'
  | 'entertainment'
  | 'social'
  | 'nature'
  | 'custom';

/** World model */
export interface World {
  id: string;
  ownerId: string;
  name: string;
  description: string;
  isPublic: boolean;
  maxCharacters: number;
  locations: Location[];
  settings: WorldSettings;
  createdAt: string;
  updatedAt: string;
}

/** Configurable world settings */
export interface WorldSettings {
  tickRate: number;
  dayLength: number;
  seasonLength: number;
  enableWeather: boolean;
  enableRandomEvents: boolean;
  difficultyModifier: number;
}

/** Payload to create a new world */
export interface WorldCreate {
  name: string;
  description?: string;
  isPublic?: boolean;
  maxCharacters?: number;
  settings?: Partial<WorldSettings>;
}
