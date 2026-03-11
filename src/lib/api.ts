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
			// Parse nested JSON error messages from skill output
			let errMsg = data.error;
			try {
				const parsed = JSON.parse(errMsg);
				errMsg = parsed.message ?? parsed.error ?? errMsg;
			} catch {
				// Not JSON, use as-is
			}
			addToast(errMsg, 'error');
			return { ...data, error: errMsg };
		}

		return data;
	} catch (err) {
		const msg = err instanceof Error ? err.message : 'Network error';
		addToast(msg, 'error');
		return { error: msg };
	}
}

/**
 * Field mappings: erpclaw response field → frontend column field.
 * Maps real DB column names to what the DataTable/mock data expects.
 */
const FIELD_MAPS: Record<string, Record<string, string>> = {
	customer: {
		customer_type: 'type',
		credit_limit: 'balance'
	},
	supplier: {
		supplier_type: 'type'
	},
	quotation: {
		naming_series: 'id',
		customer_name: 'customer',
		customer_id: 'customer',
		transaction_date: 'date',
		grand_total: 'total',
		valid_till: 'validUntil'
	},
	sales_order: {
		naming_series: 'id',
		customer_name: 'customer',
		customer_id: 'customer',
		order_date: 'date',
		grand_total: 'total',
		delivery_date: 'deliveryDate'
	},
	delivery_note: {
		naming_series: 'id',
		customer_name: 'customer',
		customer_id: 'customer',
		posting_date: 'date',
		grand_total: 'total'
	},
	sales_invoice: {
		naming_series: 'id',
		customer_name: 'customer',
		customer_id: 'customer',
		posting_date: 'date',
		grand_total: 'total',
		outstanding_amount: 'outstanding'
	},
	purchase_order: {
		naming_series: 'id',
		supplier_name: 'supplier',
		supplier_id: 'supplier',
		order_date: 'date',
		grand_total: 'total'
	},
	purchase_receipt: {
		naming_series: 'id',
		supplier_name: 'supplier',
		supplier_id: 'supplier',
		posting_date: 'date',
		grand_total: 'total'
	},
	purchase_invoice: {
		naming_series: 'id',
		supplier_name: 'supplier',
		supplier_id: 'supplier',
		posting_date: 'date',
		grand_total: 'total',
		outstanding_amount: 'outstanding'
	},
	item: {
		item_name: 'name',
		item_group_name: 'group',
		item_group_id: 'group',
		stock_uom: 'uom',
		standard_rate: 'cost'
	},
	employee: {
		naming_series: 'id',
		full_name: 'name',
		date_of_joining: 'joinDate',
		employment_type: 'type',
		department_name: 'department',
		designation_name: 'designation'
	},
	account: {
		account_number: 'number',
		root_type: 'rootType',
		is_group: 'isGroup'
	},
	warehouse: {
		warehouse_type: 'type'
	},
	journal_entry: {
		naming_series: 'id',
		posting_date: 'date',
		entry_type: 'type',
		total_debit: 'debit',
		total_credit: 'credit'
	},
	stock_entry: {
		naming_series: 'id',
		stock_entry_type: 'type',
		posting_date: 'date'
	},
	payment_entry: {
		naming_series: 'id',
		payment_type: 'type',
		posting_date: 'date',
		paid_amount: 'amount',
		party_name: 'party',
		party_id: 'party'
	},
	expense_claim: {
		naming_series: 'id',
		expense_date: 'date',
		total_amount: 'amount',
		employee_name: 'employee',
		employee_id: 'employee'
	},
	credit_note: {
		naming_series: 'id',
		customer_name: 'customer',
		customer_id: 'customer',
		posting_date: 'date',
		grand_total: 'amount',
		return_against_name: 'invoice'
	}
};

/**
 * Fields where a human-readable "name" version should override a UUID "id" version.
 * Maps target field → list of source fields in priority order.
 */
const NAME_PRIORITY: Record<string, string[]> = {
	customer: ['customer_name'],
	supplier: ['supplier_name'],
	group: ['item_group_name'],
	employee: ['employee_name'],
	party: ['party_name']
};

function mapFields(entityKey: string, rows: Record<string, unknown>[]): Record<string, unknown>[] {
	const fieldMap = FIELD_MAPS[entityKey];
	if (!fieldMap) return rows;

	return rows.map((row) => {
		const mapped: Record<string, unknown> = {};

		// Always preserve the raw UUID id for action execution
		if ('id' in row) {
			mapped._id = row.id;
		}

		// First pass: map all fields
		for (const [key, value] of Object.entries(row)) {
			const mappedKey = fieldMap[key] ?? key;
			if (!(mappedKey in mapped) || mappedKey === '_id') {
				mapped[mappedKey] = value;
			}
		}

		// Second pass: naming_series should always win over raw id for display.
		// If naming_series is empty (draft), show "DRAFT-xxxx" prefix from UUID.
		if (fieldMap.naming_series === 'id') {
			if (row.naming_series) {
				mapped.id = row.naming_series;
			} else if (row.id) {
				mapped.id = `DRAFT-${String(row.id).slice(0, 8)}`;
			}
		}

		// Third pass: prefer human-readable name fields over UUIDs
		for (const [target, sources] of Object.entries(NAME_PRIORITY)) {
			for (const src of sources) {
				if (row[src] != null && String(row[src]).trim() !== '') {
					mapped[target] = row[src];
					break;
				}
			}
		}

		return mapped;
	});
}

export interface FetchResult {
	rows: Record<string, unknown>[];
	totalCount: number;
	hasMore: boolean;
}

/**
 * Fetch list data for an entity.
 * Tries the API first, returns null if unavailable (caller falls back to mock).
 */
/**
 * Action name overrides for entities with irregular plurals or non-standard names.
 */
const ACTION_OVERRIDES: Record<string, string> = {
	stock_entry: 'list-stock-entries',
	journal_entry: 'list-journal-entries',
	payment_entry: 'list-payments',
	delivery_note: 'list-delivery-notes',
	credit_note: 'list-credit-notes'
};

export async function fetchEntityData(
	skill: string,
	entityKey: string,
	options?: { filters?: Record<string, string>; offset?: number; limit?: number }
): Promise<FetchResult | null> {
	const action = ACTION_OVERRIDES[entityKey] ?? `list-${entityKey.replace(/_/g, '-')}s`;
	const params: Record<string, unknown> = {};
	if (options?.filters) {
		Object.assign(params, options.filters);
	}
	if (options?.offset) params.offset = options.offset;
	if (options?.limit) params.limit = options.limit;

	try {
		const res = await auth.apiFetch(`/api/action/${skill}/${action}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ params })
		});

		if (!res.ok) return null;

		const data = await res.json();
		if (data.error) return null;

		// Extract array from response
		let rows: Record<string, unknown>[] | null = null;
		if (Array.isArray(data.data)) rows = data.data;
		else if (Array.isArray(data)) rows = data;
		else {
			// Check for entity-named keys (e.g. { customers: [...], total_count: 13 })
			for (const value of Object.values(data)) {
				if (Array.isArray(value) && value.length > 0) {
					rows = value as Record<string, unknown>[];
					break;
				}
			}
		}

		if (!rows) return null;

		// Map field names from erpclaw schema to frontend columns
		return {
			rows: mapFields(entityKey, rows),
			totalCount: Number(data.total_count ?? rows.length),
			hasMore: Boolean(data.has_more ?? false)
		};
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
