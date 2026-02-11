import { create } from 'zustand';
import apiClient from '@/api/client';
import type { Character, CharacterCreate, CharacterUpdate } from '@shared/types/character';

interface CharacterState {
  characters: Character[];
  selectedCharacter: Character | null;
  isLoading: boolean;
  error: string | null;
}

interface CharacterActions {
  fetchCharacters: () => Promise<void>;
  createCharacter: (data: CharacterCreate) => Promise<Character>;
  updateCharacter: (id: string, data: CharacterUpdate) => Promise<void>;
  deleteCharacter: (id: string) => Promise<void>;
  selectCharacter: (character: Character | null) => void;
  clearError: () => void;
}

export const useCharacterStore = create<CharacterState & CharacterActions>((set, get) => ({
  // State
  characters: [],
  selectedCharacter: null,
  isLoading: false,
  error: null,

  // Actions
  fetchCharacters: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get<Character[]>('/characters');
      set({ characters: response.data, isLoading: false });
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to fetch characters.';
      set({ error: message, isLoading: false });
    }
  },

  createCharacter: async (data: CharacterCreate) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<Character>('/characters', data);
      const newCharacter = response.data;
      set((state) => ({
        characters: [...state.characters, newCharacter],
        isLoading: false,
      }));
      return newCharacter;
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to create character.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  updateCharacter: async (id: string, data: CharacterUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.patch<Character>(`/characters/${id}`, data);
      const updated = response.data;
      set((state) => ({
        characters: state.characters.map((c) => (c.id === id ? updated : c)),
        selectedCharacter:
          state.selectedCharacter?.id === id ? updated : state.selectedCharacter,
        isLoading: false,
      }));
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to update character.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  deleteCharacter: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.delete(`/characters/${id}`);
      const { selectedCharacter } = get();
      set((state) => ({
        characters: state.characters.filter((c) => c.id !== id),
        selectedCharacter: selectedCharacter?.id === id ? null : selectedCharacter,
        isLoading: false,
      }));
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to delete character.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  selectCharacter: (character: Character | null) => {
    set({ selectedCharacter: character });
  },

  clearError: () => set({ error: null }),
}));
