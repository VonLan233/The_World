/**
 * Character-related type definitions for The World.
 * Shared between frontend and backend.
 */

/** Big Five personality traits, each scored 0-100 */
export interface PersonalityTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  /** Custom traits added by the user */
  custom: Record<string, number>;
}

/** Character needs/drives, each scored 0-100 */
export interface CharacterNeeds {
  hunger: number;
  energy: number;
  social: number;
  fun: number;
  hygiene: number;
  comfort: number;
}

/** Current simulation state for a character */
export interface SimState {
  needs: CharacterNeeds;
  currentActivity: string;
  currentLocation: string;
  mood: string;
  moodScore: number;
  position: { x: number; y: number };
}

/** Full character model as returned by the API */
export interface Character {
  id: string;
  userId: string;
  name: string;
  species: string;
  pronouns: string;
  age: number | null;
  description: string;
  backstory: string;
  personalityTraits: PersonalityTraits;
  interests: string[];
  skills: string[];
  avatarUrl: string | null;
  isPublic: boolean;
  simState: SimState | null;
  createdAt: string;
  updatedAt: string;
}

/** Payload to create a new character */
export interface CharacterCreate {
  name: string;
  species: string;
  pronouns: string;
  age?: number | null;
  description: string;
  backstory?: string;
  personalityTraits: PersonalityTraits;
  interests?: string[];
  skills?: string[];
  isPublic?: boolean;
}

/** Payload to partially update a character */
export interface CharacterUpdate {
  name?: string;
  species?: string;
  pronouns?: string;
  age?: number | null;
  description?: string;
  backstory?: string;
  personalityTraits?: Partial<PersonalityTraits>;
  interests?: string[];
  skills?: string[];
  avatarUrl?: string | null;
  isPublic?: boolean;
}
