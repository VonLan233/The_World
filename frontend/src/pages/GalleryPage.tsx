import { useEffect, useState } from 'react';
import CharacterCard from '@/components/character/CharacterCard';
import apiClient from '@/api/client';
import type { Character } from '@shared/types/character';
import styles from './GalleryPage.module.css';

/**
 * Public gallery page showing all public characters.
 * Includes a search bar for filtering.
 */
export default function GalleryPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPublicCharacters = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get<Character[]>('/characters/public');
        setCharacters(response.data);
      } catch {
        setError('Failed to load public characters.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPublicCharacters();
  }, []);

  const filteredCharacters = characters.filter((char) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      char.name.toLowerCase().includes(q) ||
      char.species.toLowerCase().includes(q) ||
      char.description.toLowerCase().includes(q)
    );
  });

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <h1 className={styles.title}>Character Gallery</h1>
          <p className={styles.subtitle}>
            Browse public original characters created by the community.
          </p>
        </div>

        {/* Search bar */}
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder="Search characters by name, species, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        {/* Error */}
        {error && (
          <div className={styles.error}>
            <p>{error}</p>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className={styles.loading}>
            <p>Loading gallery...</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && filteredCharacters.length === 0 && !error && (
          <div className={styles.empty}>
            {searchQuery ? (
              <p>No characters match your search.</p>
            ) : (
              <p>No public characters available yet. Be the first to share one!</p>
            )}
          </div>
        )}

        {/* Character grid */}
        {filteredCharacters.length > 0 && (
          <div className={styles.grid}>
            {filteredCharacters.map((character) => (
              <CharacterCard key={character.id} character={character} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
