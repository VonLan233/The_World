import type { CharacterNeeds } from '@shared/types/character';
import styles from './NeedsDisplay.module.css';

interface NeedsDisplayProps {
  needs: CharacterNeeds;
}

interface NeedConfig {
  key: keyof CharacterNeeds;
  label: string;
  icon: string;
}

const NEEDS: NeedConfig[] = [
  { key: 'hunger', label: 'Hunger', icon: '\u{1F35E}' },
  { key: 'energy', label: 'Energy', icon: '\u{26A1}' },
  { key: 'social', label: 'Social', icon: '\u{1F465}' },
  { key: 'fun', label: 'Fun', icon: '\u{1F3AE}' },
  { key: 'hygiene', label: 'Hygiene', icon: '\u{1F6BF}' },
  { key: 'comfort', label: 'Comfort', icon: '\u{1F6CB}' },
];

/**
 * Displays six progress bars representing a character's current needs.
 * Color-coded: green (>60), yellow (30-60), red (<30).
 */
export default function NeedsDisplay({ needs }: NeedsDisplayProps) {
  return (
    <div className={styles.container}>
      <h4 className={styles.title}>Needs</h4>
      <div className={styles.needsList}>
        {NEEDS.map(({ key, label, icon }) => {
          const value = Math.round(needs[key]);
          const colorClass = getColorClass(value);

          return (
            <div key={key} className={styles.needRow}>
              <div className={styles.needInfo}>
                <span className={styles.needIcon}>{icon}</span>
                <span className={styles.needLabel}>{label}</span>
                <span className={`${styles.needValue} ${styles[colorClass]}`}>
                  {value}%
                </span>
              </div>
              <div className={styles.barTrack}>
                <div
                  className={`${styles.barFill} ${styles[colorClass]}`}
                  style={{ width: `${value}%` }}
                  role="progressbar"
                  aria-valuenow={value}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${label}: ${value}%`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getColorClass(value: number): string {
  if (value > 60) return 'good';
  if (value > 30) return 'warning';
  return 'critical';
}
