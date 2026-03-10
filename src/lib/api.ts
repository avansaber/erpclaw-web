/**
 * API client — wraps authenticated fetch for skill actions and data.
 *
 * All action calls go through POST /api/action/{skill}/{action}.
 * Handles token refresh on 401, returns typed results.
 */

import { auth } from './auth';
import { addToast } from './toast';

interface ActionResult {
	error?: string;
	result?: unknown;
	data?: unknown[];
	[key: string]: unknown;
}

/**
 * Execute a skill action via the backend API.
 * Returns the parsed JSON result, or { error } on failure.
 */
export async function executeAction(
	skill: string,
	action: string,
	params: Record<string, unknown> = {}
): Promise<ActionResult> {
	try {
		const res = await auth.apiFetch(`/api/action/${skill}/${action}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ params })
		});

		const data = await res.json();

		if (data.error) {
			addToast(data.error, 'error');
			return data;
		}

		return data;
	} catch (err) {
		const msg = err instanceof Error ? err.message : 'Network error';
		addToast(msg, 'error');
		return { error: msg };
	}
}

/**
 * Fetch list data for an entity.
 * Tries the API first, returns null if unavailable (caller falls back to mock).
 */
export async function fetchEntityData(
	skill: string,
	entityKey: string,
	filters?: Record<string, string>
): Promise<Record<string, unknown>[] | null> {
	const action = `list-${entityKey.replace(/_/g, '-')}s`;
	const params: Record<string, unknown> = {};
	if (filters) {
		Object.assign(params, filters);
	}

	try {
		const res = await auth.apiFetch(`/api/action/${skill}/${action}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ params })
		});

		if (!res.ok) return null;

		const data = await res.json();
		if (data.error) return null;

		// ERPClaw convention: list actions return { data: [...] } or an array
		if (Array.isArray(data.data)) return data.data;
		if (Array.isArray(data)) return data;
		return null;
	} catch {
		return null; // API unavailable, fall back to mock
	}
}

/**
 * Determine the skill name for a given entity based on the action prefix.
 * Non-core entities use prefixed actions (e.g. dental-add-patient → healthclaw-dental).
 */
export function skillForAction(action: string): string {
	// Namespace prefixes map to skills
	const prefixMap: Record<string, string> = {
		dental: 'healthclaw-dental',
		prop: 'propertyclaw',
		auto: 'automotiveclaw',
		food: 'foodclaw',
		retail: 'retailclaw',
		construct: 'constructclaw',
		agri: 'agricultureclaw',
		hosp: 'hospitalityclaw',
		legal: 'legalclaw',
		nonprofit: 'nonprofitclaw'
	};

	for (const [prefix, skill] of Object.entries(prefixMap)) {
		if (action.startsWith(`${prefix}-`)) return skill;
	}

	return 'erpclaw';
}
