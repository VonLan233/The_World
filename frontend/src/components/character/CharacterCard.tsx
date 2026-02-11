import type { Character } from '@shared/types/character';
import styles from './CharacterCard.module.css';

interface CharacterCardProps {
  character: Character;
  onClick?: (character: Character) => void;
}

/**
 * Displays a summary card for a single character.
 * Shows name, species, pronouns, personality traits, and visibility.
 */
export default function CharacterCard({ character, onClick }: CharacterCardProps) {
  const traitLabels = getTopTraits(character.personalityTraits);

  return (
    <div
      className={styles.card}
      onClick={() => onClick?.(character)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick(character);
        }
      }}
    >
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.avatar}>
          {character.avatarUrl ? (
            <img
              src={character.avatarUrl}
              alt={character.name}
              className={styles.avatarImg}
            />
          ) : (
            <span className={styles.avatarPlaceholder}>
              {character.name.charAt(0).toUpperCase()}
            </span>
          )}
        </div>
        <div className={styles.headerInfo}>
          <h3 className={styles.name}>{character.name}</h3>
          <span className={styles.meta}>
            {character.species} &middot; {character.pronouns}
          </span>
        </div>
        <span
          className={`${styles.badge} ${character.isPublic ? styles.badgePublic : styles.badgePrivate}`}
        >
          {character.isPublic ? 'Public' : 'Private'}
        </span>
      </div>

      {/* Description */}
      {character.description && (
        <p className={styles.description}>{character.description}</p>
      )}

      {/* Personality trait chips */}
      {traitLabels.length > 0 && (
        <div className={styles.traits}>
          {traitLabels.map((trait) => (
            <span key={trait} className={styles.traitChip}>
              {trait}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Extract the top personality traits (Big Five > 60) as human-readable labels.
 */
function getTopTraits(traits: Character['personalityTraits']): string[] {
  const labels: string[] = [];

  const bigFive: Array<{ key: keyof Omit<typeof traits, 'custom'>; label: string }> = [
    { key: 'openness', label: 'Open' },
    { key: 'conscientiousness', label: 'Conscientious' },
    { key: 'extraversion', label: 'Extraverted' },
    { key: 'agreeableness', label: 'Agreeable' },
    { key: 'neuroticism', label: 'Neurotic' },
  ];

  for (const { key, label } of bigFive) {
    if (traits[key] > 60) {
      labels.push(label);
    } else if (traits[key] < 40) {
      // Show the opposite for low scores
      const opposites: Record<string, string> = {
        Open: 'Reserved',
        Conscientious: 'Spontaneous',
        Extraverted: 'Introverted',
        Agreeable: 'Independent',
        Neurotic: 'Stable',
      };
      labels.push(opposites[label]);
    }
  }

  // Add custom traits
  for (const [name, value] of Object.entries(traits.custom)) {
    if (value > 60) {
      labels.push(name);
    }
  }

  return labels.slice(0, 5); // Cap at 5 chips
}
