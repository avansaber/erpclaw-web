/**
 * WebSocket client — connects to /ws for real-time notifications.
 *
 * Events:
 *   action_completed: a skill action finished
 *   data_changed: entity data was modified (triggers list refresh)
 */

import { writable } from 'svelte/store';

export interface WSEvent {
	event: string;
	data: Record<string, unknown>;
	timestamp: string;
}

type EventHandler = (data: Record<string, unknown>) => void;

const listeners = new Map<string, Set<EventHandler>>();

export const wsConnected = writable(false);

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let pingTimer: ReturnType<typeof setInterval> | null = null;

function getWsUrl(): string {
	const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	return `${proto}//${window.location.host}/ws`;
}

function handleMessage(raw: string) {
	try {
		const msg: WSEvent = JSON.parse(raw);
		if (msg.event === 'pong') return;

		const handlers = listeners.get(msg.event);
		if (handlers) {
			for (const handler of handlers) {
				try {
					handler(msg.data);
				} catch {
					// Ignore handler errors
				}
			}
		}
	} catch {
		// Ignore non-JSON messages
	}
}

export function connectWS() {
	if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
		return;
	}

	try {
		ws = new WebSocket(getWsUrl());
	} catch {
		scheduleReconnect();
		return;
	}

	ws.onopen = () => {
		wsConnected.set(true);
		// Ping every 30s to keep connection alive
		pingTimer = setInterval(() => {
			if (ws?.readyState === WebSocket.OPEN) {
				ws.send('ping');
			}
		}, 30_000);
	};

	ws.onmessage = (e) => handleMessage(e.data);

	ws.onclose = () => {
		wsConnected.set(false);
		cleanup();
		scheduleReconnect();
	};

	ws.onerror = () => {
		wsConnected.set(false);
	};
}

function cleanup() {
	if (pingTimer) {
		clearInterval(pingTimer);
		pingTimer = null;
	}
}

function scheduleReconnect() {
	if (reconnectTimer) return;
	reconnectTimer = setTimeout(() => {
		reconnectTimer = null;
		connectWS();
	}, 5_000);
}

export function disconnectWS() {
	if (reconnectTimer) {
		clearTimeout(reconnectTimer);
		reconnectTimer = null;
	}
	cleanup();
	if (ws) {
		ws.close();
		ws = null;
	}
	wsConnected.set(false);
}

/**
 * Subscribe to a WebSocket event. Returns an unsubscribe function.
 */
export function onWSEvent(event: string, handler: EventHandler): () => void {
	if (!listeners.has(event)) {
		listeners.set(event, new Set());
	}
	listeners.get(event)!.add(handler);

	return () => {
		listeners.get(event)?.delete(handler);
	};
}
