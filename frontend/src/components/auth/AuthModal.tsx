import { useState, useEffect, useCallback, type FormEvent } from 'react';
import { createPortal } from 'react-dom';
import { useAuthStore } from '@/stores/useAuthStore';
import styles from './AuthModal.module.css';

type AuthMode = 'login' | 'register';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: AuthMode;
}

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

/**
 * Auth modal supporting Login and Register flows.
 * Rendered via React portal into document.body for correct z-index stacking.
 */
export default function AuthModal({ isOpen, onClose, initialMode = 'login' }: AuthModalProps) {
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [visible, setVisible] = useState(false);

  // Form fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Client-side validation errors
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // API-level error displayed at the top
  const [apiError, setApiError] = useState<string | null>(null);

  // Sync initialMode when the parent changes it while the modal is re-opened
  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
    }
  }, [initialMode, isOpen]);

  // Animate in / out
  useEffect(() => {
    if (isOpen) {
      // Reset state when opening
      setUsername('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setFormErrors({});
      setApiError(null);
      clearError();

      // Trigger entrance animation on the next frame
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setVisible(true);
        });
      });
    } else {
      setVisible(false);
    }
  }, [isOpen, clearError]);

  // Escape key handler
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    },
    [isOpen, onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Switch between tabs
  const switchMode = (newMode: AuthMode) => {
    if (newMode === mode) return;
    setMode(newMode);
    setFormErrors({});
    setApiError(null);
    clearError();
  };

  // Validation
  const validate = (): boolean => {
    const errors: FormErrors = {};

    if (!username.trim()) {
      errors.username = 'Username is required.';
    }

    if (mode === 'register') {
      if (!email.trim()) {
        errors.email = 'Email is required.';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.email = 'Please enter a valid email address.';
      }
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters.';
    }

    if (mode === 'register') {
      if (!confirmPassword) {
        errors.confirmPassword = 'Please confirm your password.';
      } else if (password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match.';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setApiError(null);
    clearError();

    if (!validate()) return;

    try {
      if (mode === 'login') {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), email.trim(), password);
      }
      // Success -- close modal
      onClose();
    } catch (err) {
      // The store already sets its own error, but we also capture it locally
      // so it survives potential store resets.
      const message =
        err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setApiError(message);
    }
  };

  // Overlay click
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  const displayError = apiError || error;

  const modal = (
    <div
      className={`${styles.overlay} ${visible ? styles.overlayVisible : ''}`}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-label={mode === 'login' ? 'Login' : 'Create account'}
    >
      <div className={`${styles.modal} ${visible ? styles.modalVisible : ''}`}>
        {/* Close button */}
        <button
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="Close modal"
          type="button"
        >
          &#x2715;
        </button>

        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <p className={styles.subtitle}>
            {mode === 'login'
              ? 'Sign in to continue your journey'
              : 'Join The World and start exploring'}
          </p>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${mode === 'login' ? styles.tabActive : ''}`}
            onClick={() => switchMode('login')}
            type="button"
          >
            Login
          </button>
          <button
            className={`${styles.tab} ${mode === 'register' ? styles.tabActive : ''}`}
            onClick={() => switchMode('register')}
            type="button"
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate>
          <div className={styles.body}>
            {/* API error */}
            {displayError && (
              <div className={styles.error}>
                <span className={styles.errorIcon}>!</span>
                <span>{displayError}</span>
              </div>
            )}

            {/* Username */}
            <div className={styles.field}>
              <label className={styles.label} htmlFor="auth-username">
                Username
              </label>
              <input
                id="auth-username"
                className={`${styles.input} ${formErrors.username ? styles.inputError : ''}`}
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
              />
              {formErrors.username && (
                <div className={styles.fieldError}>{formErrors.username}</div>
              )}
            </div>

            {/* Email (register only) */}
            {mode === 'register' && (
              <div className={styles.field}>
                <label className={styles.label} htmlFor="auth-email">
                  Email
                </label>
                <input
                  id="auth-email"
                  className={`${styles.input} ${formErrors.email ? styles.inputError : ''}`}
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
                {formErrors.email && (
                  <div className={styles.fieldError}>{formErrors.email}</div>
                )}
              </div>
            )}

            {/* Password */}
            <div className={styles.field}>
              <label className={styles.label} htmlFor="auth-password">
                Password
              </label>
              <input
                id="auth-password"
                className={`${styles.input} ${formErrors.password ? styles.inputError : ''}`}
                type="password"
                placeholder={mode === 'login' ? 'Enter your password' : 'At least 6 characters'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              {formErrors.password && (
                <div className={styles.fieldError}>{formErrors.password}</div>
              )}
            </div>

            {/* Confirm password (register only) */}
            {mode === 'register' && (
              <div className={styles.field}>
                <label className={styles.label} htmlFor="auth-confirm-password">
                  Confirm Password
                </label>
                <input
                  id="auth-confirm-password"
                  className={`${styles.input} ${formErrors.confirmPassword ? styles.inputError : ''}`}
                  type="password"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                />
                {formErrors.confirmPassword && (
                  <div className={styles.fieldError}>{formErrors.confirmPassword}</div>
                )}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isLoading}
            >
              {isLoading && <span className={styles.spinner} />}
              {isLoading
                ? mode === 'login'
                  ? 'Signing in...'
                  : 'Creating account...'
                : mode === 'login'
                  ? 'Sign In'
                  : 'Create Account'}
            </button>
          </div>
        </form>

        {/* Footer toggle */}
        <div className={styles.footer}>
          {mode === 'login' ? (
            <span>
              Don&apos;t have an account?{' '}
              <button
                className={styles.switchBtn}
                onClick={() => switchMode('register')}
                type="button"
              >
                Sign up
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{' '}
              <button
                className={styles.switchBtn}
                onClick={() => switchMode('login')}
                type="button"
              >
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
