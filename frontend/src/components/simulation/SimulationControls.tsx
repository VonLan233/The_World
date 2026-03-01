import styles from './SimulationControls.module.css';

const SPEED_OPTIONS = [1, 2, 5];

interface SimulationControlsProps {
  isRunning: boolean;
  currentHour: number;
  currentDay: number;
  currentSeason: string;
  speed: number;
  onToggle: () => void;
  onSpeedChange: (speed: number) => void;
}

function formatTime(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`;
}

function seasonIcon(s: string): string {
  switch (s) {
    case 'spring': return '\u{1F338}';
    case 'summer': return '\u{2600}\u{FE0F}';
    case 'autumn': return '\u{1F342}';
    case 'winter': return '\u{2744}\u{FE0F}';
    default: return '';
  }
}

export default function SimulationControls({
  isRunning,
  currentHour,
  currentDay,
  currentSeason,
  speed,
  onToggle,
  onSpeedChange,
}: SimulationControlsProps) {
  return (
    <div className={styles.section}>
      <h3 className={styles.title}>Simulation</h3>
      <div className={styles.clockInfo}>
        <div className={styles.clockMain}>
          <span className={styles.clockTimeDisplay}>{formatTime(currentHour)}</span>
          <span className={styles.clockDayDisplay}>
            Day {currentDay} {seasonIcon(currentSeason)} {currentSeason}
          </span>
        </div>
      </div>

      <div className={styles.controls}>
        <button
          className={`${styles.toggleBtn} ${isRunning ? styles.toggleRunning : ''}`}
          onClick={onToggle}
        >
          {isRunning ? '\u23F8 Pause' : '\u25B6 Play'}
        </button>

        <div className={styles.speedControls}>
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              className={`${styles.speedBtn} ${speed === s ? styles.speedActive : ''}`}
              onClick={() => onSpeedChange(s)}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
