import { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/useAuthStore';
import AuthModal from '@/components/auth/AuthModal';
import styles from './Header.module.css';

/**
 * Top navigation header.
 * Shows app title, navigation links, and auth controls.
 * Login/Register buttons open a modal instead of navigating to separate pages.
 */
export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  const openAuthModal = useCallback((mode: 'login' | 'register') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <>
      <header className={styles.header}>
        <div className={styles.inner}>
          {/* Brand */}
          <Link to="/" className={styles.brand}>
            <span className={styles.brandIcon}>&#x2726;</span>
            <span className={styles.brandText}>The World</span>
          </Link>

          {/* Navigation */}
          <nav className={styles.nav}>
            <Link to="/" className={styles.navLink}>
              Home
            </Link>
            <Link to="/dashboard" className={styles.navLink}>
              Dashboard
            </Link>
            <Link to="/gallery" className={styles.navLink}>
              Gallery
            </Link>
          </nav>

          {/* Auth controls */}
          <div className={styles.auth}>
            {isAuthenticated && user ? (
              <div className={styles.userMenu}>
                <span className={styles.username}>{user.username}</span>
                <button onClick={handleLogout} className={styles.logoutBtn}>
                  Logout
                </button>
              </div>
            ) : (
              <div className={styles.authButtons}>
                <button
                  onClick={() => openAuthModal('login')}
                  className={styles.loginBtn}
                >
                  Login
                </button>
                <button
                  onClick={() => openAuthModal('register')}
                  className={styles.registerBtn}
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={closeAuthModal}
        initialMode={authModalMode}
      />
    </>
  );
}
