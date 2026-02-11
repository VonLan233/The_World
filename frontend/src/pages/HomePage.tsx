import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.css';

/**
 * Landing page with hero section, feature cards, and CTA.
 */
export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>The World</h1>
          <p className={styles.heroTagline}>Give your OC a life.</p>
          <p className={styles.heroDescription}>
            An AI-powered life simulation platform where your original characters
            live, work, socialize, and grow -- all on their own. Create detailed
            characters, drop them into shared worlds, and watch emergent stories
            unfold.
          </p>
          <button
            className={styles.ctaButton}
            onClick={() => navigate('/dashboard')}
          >
            Get Started
          </button>
        </div>
        <div className={styles.heroVisual}>
          <div className={styles.orb} />
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>&#x270D;</div>
            <h3 className={styles.featureTitle}>Create</h3>
            <p className={styles.featureDescription}>
              Build rich characters with personality traits, backstories,
              interests, and skills. Import existing OCs from character sheets or
              description text.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>&#x2699;</div>
            <h3 className={styles.featureTitle}>Simulate</h3>
            <p className={styles.featureDescription}>
              Watch your characters make autonomous decisions driven by AI. They
              eat, sleep, work, play, and form relationships -- just like real
              life.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>&#x1F310;</div>
            <h3 className={styles.featureTitle}>Connect</h3>
            <p className={styles.featureDescription}>
              Place your characters into shared worlds alongside others. See how
              different OCs interact and build unexpected friendships and
              rivalries.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
