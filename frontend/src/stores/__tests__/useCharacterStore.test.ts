import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCharacterStore } from '../useCharacterStore';

vi.mock('@/api/client', () => {
  const get = vi.fn();
  const post = vi.fn();
  const patch = vi.fn();
  const del = vi.fn();
  return {
    default: { get, post, patch, delete: del },
  };
});

import apiClient from '@/api/client';

const mockedGet = vi.mocked(apiClient.get);
const mockedPatch = vi.mocked(apiClient.patch);

const baseCharacter = {
  id: 'c1',
  userId: 'u1',
  name: 'Alice',
  description: 'Desc',
  species: 'human',
  age: 20,
  pronouns: 'she/her',
  avatarUrl: null,
  personalityTraits: {
    openness: 50,
    conscientiousness: 50,
    extraversion: 50,
    agreeableness: 50,
    neuroticism: 50,
    custom: {},
  },
  backstory: '',
  interests: [],
  skills: [],
  isPublic: true,
  simState: null,
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-01T00:00:00Z',
};

beforeEach(() => {
  useCharacterStore.setState({
    characters: [],
    selectedCharacter: null,
    isLoading: false,
    error: null,
  });
  vi.clearAllMocks();
});

describe('useCharacterStore', () => {
  it('fetchCharacters loads character list', async () => {
    mockedGet.mockResolvedValueOnce({ data: [baseCharacter] } as never);

    await useCharacterStore.getState().fetchCharacters();

    const state = useCharacterStore.getState();
    expect(state.characters).toHaveLength(1);
    expect(state.characters[0]?.id).toBe('c1');
    expect(mockedGet).toHaveBeenCalledWith('/characters');
  });

  it('updateCharacter uses PATCH endpoint and updates state', async () => {
    useCharacterStore.setState({
      characters: [baseCharacter],
      selectedCharacter: baseCharacter,
    });

    const updated = { ...baseCharacter, name: 'Alice Updated' };
    mockedPatch.mockResolvedValueOnce({ data: updated } as never);

    await useCharacterStore.getState().updateCharacter('c1', { name: 'Alice Updated' });

    expect(mockedPatch).toHaveBeenCalledWith('/characters/c1', { name: 'Alice Updated' });
    const state = useCharacterStore.getState();
    expect(state.characters[0]?.name).toBe('Alice Updated');
    expect(state.selectedCharacter?.name).toBe('Alice Updated');
  });
});
