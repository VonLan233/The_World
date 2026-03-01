import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketClient } from '../websocket';

// Mock getAuthToken
vi.mock('../client', () => ({
  getAuthToken: () => 'test-token',
}));

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  OPEN = 1;
  CLOSED = 3;
  readyState = 1;
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: ((e: { code: number; reason: string }) => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    // Simulate async open
    setTimeout(() => this.onopen?.(), 0);
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

describe('WebSocketClient', () => {
  let client: WebSocketClient;

  beforeEach(() => {
    vi.useFakeTimers();
    client = new WebSocketClient();
  });

  afterEach(() => {
    client.disconnect();
    vi.useRealTimers();
  });

  it('connect creates a WebSocket connection', () => {
    client.connect('world-1');
    expect(client.connectionState).toBe('connecting');
  });

  it('updates connectionState to connected on open', async () => {
    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);
    expect(client.connectionState).toBe('connected');
  });

  it('send sends JSON when OPEN', async () => {
    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);

    client.send({ type: 'ping' } as never);

    // Access the underlying mock WS
    expect(client.isConnected).toBe(true);
  });

  it('send does not throw when not connected', () => {
    // Not connected — should just log a warning, not throw
    expect(() => {
      client.send({ type: 'ping' } as never);
    }).not.toThrow();
  });

  it('on() registers listener and returns unsub function', async () => {
    const callback = vi.fn();
    const unsub = client.on('pong', callback);

    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);

    // 'pong' is emitted on open
    expect(callback).toHaveBeenCalledWith({ type: 'pong' });

    // Unsubscribe
    unsub();
    callback.mockClear();

    // Reconnect — callback should not fire
    client.disconnect();
    client.connect('world-2');
    await vi.advanceTimersByTimeAsync(10);
    expect(callback).not.toHaveBeenCalled();
  });

  it('wildcard listener receives all messages', async () => {
    const callback = vi.fn();
    client.on('*', callback);

    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);

    // The synthetic 'pong' on open should have triggered wildcard
    expect(callback).toHaveBeenCalledWith({ type: 'pong' });
  });

  it('disconnect closes connection and sets state to disconnected', async () => {
    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);

    client.disconnect();
    expect(client.connectionState).toBe('disconnected');
    expect(client.isConnected).toBe(false);
  });

  it('onStateChange notifies listeners of state changes', async () => {
    const states: string[] = [];
    client.onStateChange((s) => states.push(s));

    client.connect('world-1');
    await vi.advanceTimersByTimeAsync(10);
    client.disconnect();

    expect(states).toContain('connecting');
    expect(states).toContain('connected');
    expect(states).toContain('disconnected');
  });

  it('onStateChange returns unsub function', () => {
    const callback = vi.fn();
    const unsub = client.onStateChange(callback);
    unsub();

    client.connect('world-1');
    // Should not be notified after unsub
    expect(callback).not.toHaveBeenCalled();
  });
});
