import { useEffect } from 'react';
import { useRelationshipStore } from '@/stores/useRelationshipStore';
import type { RelationshipSummary } from '@shared/types/relationship';
import styles from './RelationshipPanel.module.css';

interface Props {
  characterId: string | null;
}

function getBarColor(score: number, type: string): string {
  if (type === 'romantic') return styles.romantic;
  if (score < 0) return styles.negative;
  return styles.positive;
}

function RelationshipItem({ rel }: { rel: RelationshipSummary }) {
  // Map score from [-100, 100] to [0, 100] for bar width
  const barWidth = Math.abs(rel.friendshipScore);
  const typeClass = styles[rel.relationshipType as keyof typeof styles] ?? '';

  return (
    <div className={styles.item}>
      <div className={styles.info}>
        <span className={styles.name}>{rel.targetName}</span>
        <span className={`${styles.type} ${typeClass}`}>
          {rel.relationshipType.replace('_', ' ')}
        </span>
        <span className={styles.score}>{Math.round(rel.friendshipScore)}</span>
      </div>
      <div className={styles.barTrack}>
        <div
          className={`${styles.barFill} ${getBarColor(rel.friendshipScore, rel.relationshipType)}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  );
}

export default function RelationshipPanel({ characterId }: Props) {
  const { relationships, fetchRelationships } = useRelationshipStore();

  useEffect(() => {
    if (characterId) {
      fetchRelationships(characterId);
    }
  }, [characterId, fetchRelationships]);

  const rels = characterId ? relationships.get(characterId) ?? [] : [];

  return (
    <div className={styles.container}>
      <h4 className={styles.title}>Relationships</h4>
      {rels.length === 0 ? (
        <p className={styles.placeholder}>No relationships yet.</p>
      ) : (
        <div className={styles.list}>
          {rels.map((rel) => (
            <RelationshipItem key={rel.targetId} rel={rel} />
          ))}
        </div>
      )}
    </div>
  );
}
