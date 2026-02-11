import type { WSClientMessage, WSServerMessage } from '@shared/types/events';
import { getAuthToken } from './client';

type EventCallback = (data: WSServerMessage) => void;

/**
 * WebSocket client for real-time simulation communication.
 * Supports auto-reconnect, typed messaging, and event handling.
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;
  private currentWorldId: string | null = null;

  /**
   * Establish a WebSocket connection to a world simulation.
   */
  connect(worldId: string): void {
    this.currentWorldId = worldId;
    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    this.createConnection(worldId);
  }

  /**
   * Disconnect and stop auto-reconnect.
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.currentWorldId = null;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
  }

  /**
   * Register an event handler for a specific server message type.
   * Pass '*' to listen to all messages.
   */
  on(eventType: WSServerMessage['type'] | '*', callback: EventCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);

    // Return an unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }

  /**
   * Send a typed message to the server.
   */
  send(data: WSClientMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WS] Cannot send message, WebSocket is not connected');
    }
  }

  /** Whether the WebSocket is currently connected */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  // -- Private --

  private createConnection(worldId: string): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = getAuthToken();
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    const url = `${protocol}//${host}/ws/world/${worldId}${tokenParam}`;

    try {
      this.ws = new WebSocket(url);
    } catch (err) {
      console.error('[WS] Failed to create WebSocket:', err);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log(`[WS] Connected to world ${worldId}`);
      this.reconnectAttempts = 0;
      this.emit({ type: 'pong' } as WSServerMessage); // Notify listeners of connection
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSServerMessage;
        this.emit(message);
      } catch (err) {
        console.error('[WS] Failed to parse message:', err);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code: ${event.code}, reason: ${event.reason})`);
      this.ws = null;

      if (this.shouldReconnect && event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (event) => {
      console.error('[WS] Error:', event);
    };
  }

  private emit(message: WSServerMessage): void {
    // Notify specific type listeners
    const typeListeners = this.listeners.get(message.type);
    if (typeListeners) {
      typeListeners.forEach((cb) => cb(message));
    }

    // Notify wildcard listeners
    const wildcardListeners = this.listeners.get('*');
    if (wildcardListeners) {
      wildcardListeners.forEach((cb) => cb(message));
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached, giving up');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    const jitter = delay * 0.2 * Math.random();
    const totalDelay = Math.min(delay + jitter, 30000);

    console.log(
      `[WS] Reconnecting in ${Math.round(totalDelay)}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`,
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      if (this.currentWorldId) {
        this.createConnection(this.currentWorldId);
      }
    }, totalDelay);
  }
}

/** Singleton WebSocket client instance */
export const wsClient = new WebSocketClient();
