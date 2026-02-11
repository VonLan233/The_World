import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCharacterStore } from '@/stores/useCharacterStore';
import CharacterCard from '@/components/character/CharacterCard';
import type { Character } from '@shared/types/character';
import styles from './DashboardPage.module.css';

/**
 * User dashboard: lists the user's characters and allows creation of new ones.
 */
export default function DashboardPage() {
  const navigate = useNavigate();
  const { characters, isLoading, error, fetchCharacters } = useCharacterStore();

  useEffect(() => {
    fetchCharacters();
  }, [fetchCharacters]);

  const handleCharacterClick = (character: Character) => {
    navigate(`/world/default`, { state: { characterId: character.id } });
  };

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
