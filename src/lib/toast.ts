/**
 * Toast notification store — lightweight, no external deps.
 */

import { writable } from 'svelte/store';

export interface Toast {
	id: number;
	message: string;
	type: 'success' | 'error' | 'info';
}

let nextId = 0;

export const toasts = writable<Toast[]>([]);

export function addToast(message: string, type: Toast['type'] = 'info', duration = 4000) {
	const id = nextId++;
	toasts.update((t) => [...t, { id, message, type }]);

	if (duration > 0) {
		setTimeout(() => removeToast(id), duration);
	}
}

export function removeToast(id: number) {
	toasts.update((t) => t.filter((toast) => toast.id !== id));
}
