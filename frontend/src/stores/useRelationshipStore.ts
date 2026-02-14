import { create } from 'zustand';
import apiClient from '@/api/client';
import type { RelationshipSummary } from '@shared/types/relationship';

interface RelationshipState {
  /** Map from characterId → list of relationship summaries */
  relationships: Map<string, RelationshipSummary[]>;
}

interface RelationshipActions {
  fetchRelationships: (characterId: string) => Promise<void>;
  updateRelationshipFromEvent: (data: {
    characterId: string;
    targetId: string;
    targetName: string;
    friendshipScore: number;
    relationshipType: string;
  }) => void;
  clear: () => void;
}

export const useRelationshipStore = create<RelationshipState & RelationshipActions>(
  (set) => ({
    relationships: new Map(),

    fetchRelationships: async (characterId: string) => {
      try {
        const resp = await apiClient.get(`/relationships/${characterId}`);
        const data = resp.data;
        set((state) => {
          const newMap = new Map(state.relationships);
          newMap.set(characterId, data.relationships ?? []);
          return { relationships: newMap };
        });
      } catch {
        // Silently ignore fetch errors (character may have no relationships)
      }
    },

    updateRelationshipFromEvent: (data) => {
      set((state) => {
        const newMap = new Map(state.relationships);
        const existing = newMap.get(data.characterId) ?? [];

        const idx = existing.findIndex((r) => r.targetId === data.targetId);
        const updated: RelationshipSummary = {
          targetId: data.targetId,
          targetName: data.targetName,
          relationshipType: data.relationshipType as RelationshipSummary['relationshipType'],
          friendshipScore: data.friendshipScore,
        };

        if (idx >= 0) {
          const copy = [...existing];
          copy[idx] = updated;
          newMap.set(data.characterId, copy);
        } else {
          newMap.set(data.characterId, [...existing, updated]);
        }

        return { relationships: newMap };
      });
    },

    clear: () => {
      set({ relationships: new Map() });
    },
  }),
);
