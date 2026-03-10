/**
 * Auth store — manages JWT tokens, login/logout, authenticated fetch.
 *
 * Tokens stored in memory (access) + httpOnly cookie (refresh, managed by server).
 * Access token is NOT in localStorage to prevent XSS theft.
 */

import { writable, derived } from 'svelte/store';

export interface AuthUser {
	id: string;
	username: string;
	email: string;
	full_name: string;
	roles: string[];
}

interface AuthState {
	user: AuthUser | null;
	accessToken: string | null;
	loading: boolean;
	setupRequired: boolean | null;
}

const state = writable<AuthState>({
	user: null,
	accessToken: null,
	loading: true,
	setupRequired: null
});

export const auth = {
	subscribe: state.subscribe,

	/** Check if initial setup is needed */
	async checkSetup(): Promise<boolean> {
		try {
			const res = await fetch('/api/auth/check-setup');
			const data = await res.json();
			const required = data.setup_required ?? false;
			state.update((s) => ({ ...s, setupRequired: required }));
			return required;
		} catch {
			// API not available — fall back to mock mode
			state.update((s) => ({ ...s, setupRequired: null, loading: false }));
			return false;
		}
	},

	/** Initial setup — create first admin user */
	async setup(username: string, email: string, full_name: string, password: string) {
		const res = await fetch('/api/auth/setup', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username, email, full_name, password })
		});
		return res.json();
	},

	/** Login with email + password */
	async login(email: string, password: string): Promise<{ ok: boolean; error?: string }> {
		try {
			const res = await fetch('/api/auth/login', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({ email, password })
			});
			const data = await res.json();

			if (data.error) {
				return { ok: false, error: data.error };
			}

			state.update((s) => ({
				...s,
				user: data.user,
				accessToken: data.access_token,
				loading: false
			}));
			return { ok: true };
		} catch {
			return { ok: false, error: 'Could not connect to server' };
		}
	},

	/** Try to restore session from refresh cookie */
	async refresh(): Promise<boolean> {
		try {
			const res = await fetch('/api/auth/refresh', {
				method: 'POST',
				credentials: 'include'
			});
			const data = await res.json();

			if (data.error) {
				state.update((s) => ({ ...s, user: null, accessToken: null, loading: false }));
				return false;
			}

			// Get user info with the new token
			const meRes = await fetch('/api/auth/me', {
				headers: { Authorization: `Bearer ${data.access_token}` }
			});
			const meData = await meRes.json();

			state.update((s) => ({
				...s,
				user: meData.user ?? null,
				accessToken: data.access_token,
				loading: false
			}));
			return !!meData.user;
		} catch {
			state.update((s) => ({ ...s, user: null, accessToken: null, loading: false }));
			return false;
		}
	},

	/** Logout */
	async logout() {
		try {
			await fetch('/api/auth/logout', {
				method: 'POST',
				credentials: 'include'
			});
		} catch {
			// Ignore — clear local state regardless
		}
		state.update((s) => ({
			...s,
			user: null,
			accessToken: null,
			loading: false
		}));
	},

	/** Authenticated fetch — auto-attaches token, handles 401 refresh */
	async apiFetch(url: string, init?: RequestInit): Promise<Response> {
		let token: string | null = null;
		state.subscribe((s) => (token = s.accessToken))();

		const headers = new Headers(init?.headers);
		if (token) {
			headers.set('Authorization', `Bearer ${token}`);
		}

		let res = await fetch(url, { ...init, headers, credentials: 'include' });

		// If 401, try refreshing the token once (even if token was null — handles full page reload race)
		if (res.status === 401) {
			const refreshed = await auth.refresh();
			if (refreshed) {
				state.subscribe((s) => (token = s.accessToken))();
				headers.set('Authorization', `Bearer ${token}`);
				res = await fetch(url, { ...init, headers, credentials: 'include' });
			}
		}

		return res;
	}
};

/** Derived stores for convenience */
export const user = derived(state, ($s) => $s.user);
export const isAuthenticated = derived(state, ($s) => !!$s.user);
export const isLoading = derived(state, ($s) => $s.loading);
export const userRoles = derived(state, ($s) => $s.user?.roles ?? []);
