import { createPortal } from 'react-dom';
import { useToastStore } from '@/stores/useToastStore';
import styles from './Toast.module.css';

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return createPortal(
    <div className={styles.container}>
      {toasts.map((toast) => (
        <div key={toast.id} className={`${styles.toast} ${styles[toast.type]}`}>
          <span className={styles.message}>{toast.message}</span>
          <button className={styles.close} onClick={() => removeToast(toast.id)}>
            &times;
          </button>
        </div>
      ))}
    </div>,
    document.body,
  );
}
