import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { wsClient, type ConnectionState } from '@/api/websocket';
import styles from './ConnectionStatus.module.css';

const LABELS: Record<ConnectionState, string> = {
  disconnected: 'Disconnected',
  connecting: 'Connecting...',
  connected: 'Connected',
  reconnecting: 'Reconnecting...',
};

export default function ConnectionStatus() {
  const location = useLocation();
  const [state, setState] = useState<ConnectionState>(wsClient.connectionState);

  useEffect(() => {
    return wsClient.onStateChange(setState);
  }, []);

  if (!location.pathname.startsWith('/world/')) return null;

  return (
    <div className={`${styles.status} ${styles[state]}`}>
      <span className={styles.dot} />
      <span className={styles.label}>{LABELS[state]}</span>
    </div>
  );
}
