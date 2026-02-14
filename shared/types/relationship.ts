/**
 * Relationship type definitions for The World.
 */

/** Relationship classification labels */
export type RelationshipType =
  | 'stranger'
  | 'acquaintance'
  | 'friend'
  | 'close_friend'
  | 'romantic'
  | 'rival';

/** Full relationship data from the API */
export interface Relationship {
  id: string;
  sourceCharacterId: string;
  targetCharacterId: string;
  friendshipScore: number;
  romanceScore: number;
  rivalryScore: number;
  relationshipType: RelationshipType;
  compatibility: number | null;
  createdAt: string;
  updatedAt: string;
}

/** Lightweight relationship summary for list views */
export interface RelationshipSummary {
  targetId: string;
  targetName: string;
  relationshipType: RelationshipType;
  friendshipScore: number;
}

/** API response for listing relationships */
export interface RelationshipListResponse {
  characterId: string;
  relationships: RelationshipSummary[];
}
