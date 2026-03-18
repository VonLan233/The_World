import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '@/api/client';
import { useCharacterStore } from '@/stores/useCharacterStore';
import { useAuthStore } from '@/stores/useAuthStore';
import CharacterCard from '@/components/character/CharacterCard';
import type { Character } from '@shared/types/character';
import styles from './DashboardPage.module.css';

interface WorldInfo {
  id: string;
  name: string;
}

/**
 * User dashboard: lists the user's characters and allows creation of new ones.
 */
export default function DashboardPage() {
  const navigate = useNavigate();
  const { characters, isLoading, error, fetchCharacters } = useCharacterStore();
  const { isAuthenticated, isInitializing } = useAuthStore();
  const [worlds, setWorlds] = useState<WorldInfo[]>([]);

  useEffect(() => {
    if (isInitializing) return;
    if (!isAuthenticated) {
      navigate('/');
      return;
    }
    fetchCharacters();
    apiClient.get<WorldInfo[]>('/worlds').then((res) => setWorlds(res.data)).catch(() => {});
  }, [fetchCharacters, isAuthenticated, isInitializing, navigate]);

  const handleCharacterClick = async (character: Character) => {
    let worldId: string;
    if (worlds.length > 0) {
      worldId = worlds[0].id;
    } else {
      const res = await apiClient.post<WorldInfo>('/worlds/');
      worldId = res.data.id;
      setWorlds([res.data]);
    }
    navigate(`/world/setup/${worldId}`, { state: { characterId: character.id } });
  };

  if (isInitializing) {
    return <div className={styles.page}><div className={styles.loading}><p>Loading...</p></div></div>;
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>My Characters</h1>
            <p className={styles.subtitle}>
              Manage your original characters and drop them into worlds.
            </p>
          </div>
          <button
            className={styles.createBtn}
            onClick={() => navigate('/character/create')}
          >
            + Create New Character
          </button>
        </div>

        {/* Error state */}
        {error && (
          <div className={styles.error}>
            <p>{error}</p>
          </div>
        )}

        {/* Loading state */}
        {isLoading && characters.length === 0 && (
          <div className={styles.loading}>
            <p>Loading characters...</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && characters.length === 0 && !error && (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>&#x2726;</div>
            <h3>No characters yet</h3>
            <p>Create your first original character to get started.</p>
            <button
              className={styles.createBtn}
              onClick={() => navigate('/character/create')}
            >
              Create Character
            </button>
          </div>
        )}

        {/* Character grid */}
        {characters.length > 0 && (
          <div className={styles.grid}>
            {characters.map((character) => (
              <CharacterCard
                key={character.id}
                character={character}
                onClick={handleCharacterClick}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
