import { useNavigate } from 'react-router-dom';
import styles from './CharacterCreatePage.module.css';

/**
 * Character creation page placeholder.
 * Will contain a multi-step form for building a new OC.
 */
export default function CharacterCreatePage() {
  const navigate = useNavigate();

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={() => navigate('/dashboard')}>
            &larr; Back to Dashboard
          </button>
          <h1 className={styles.title}>Create Character</h1>
          <p className={styles.subtitle}>
            Bring a new original character to life. Fill in their details and
            personality, then drop them into a world.
          </p>
        </div>

        <div className={styles.placeholder}>
          <div className={styles.placeholderIcon}>&#x270D;</div>
          <h3>Character Creator Coming Soon</h3>
          <p>
            The full character creation form with personality sliders, backstory
            editor, and AI-assisted generation will be built here.
          </p>
        </div>
      </div>
    </div>
  );
}
