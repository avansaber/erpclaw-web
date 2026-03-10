import { describe, it, expect } from 'vitest';
import type { VerticalLayout, EntityDef, ColumnDef, FormSpec } from '$lib/types';
import { erpclaw } from '$lib/mock/erpclaw';
import { dental } from '$lib/mock/dental';
import { property } from '$lib/mock/property';

// Test all three verticals against the VerticalLayout contract
const verticals: [string, VerticalLayout][] = [
	['erpclaw', erpclaw],
	['dental', dental],
	['property', property]
];

describe.each(verticals)('VerticalLayout: %s', (name, layout) => {
	it('has required top-level fields', () => {
		expect(layout.name).toBe(name);
		expect(layout.label).toBeTruthy();
		expect(layout.description).toBeTruthy();
		expect(layout.icon).toBeTruthy();
		expect(layout.color).toMatch(/^#[0-9a-f]{6}$/i);
	});

	it('has at least 1 KPI', () => {
		expect(layout.kpis.length).toBeGreaterThanOrEqual(1);
		for (const kpi of layout.kpis) {
			expect(kpi.label).toBeTruthy();
			expect(kpi.value).toBeTruthy();
			expect(kpi.sub).toBeTruthy();
			expect(kpi.color).toMatch(/^#[0-9a-f]{6}$/i);
		}
	});

	it('has at least 1 workflow with steps', () => {
		expect(layout.workflows.length).toBeGreaterThanOrEqual(1);
		for (const wf of layout.workflows) {
			expect(wf.key).toBeTruthy();
			expect(wf.label).toBeTruthy();
			expect(wf.icon).toBeTruthy();
			expect(wf.primaryAction).toBeTruthy();
			expect(wf.steps.length).toBeGreaterThanOrEqual(2);
		}
	});

	it('has sidebar groups with items', () => {
		expect(layout.sidebar.length).toBeGreaterThanOrEqual(1);
		for (const group of layout.sidebar) {
			expect(group.label).toBeTruthy();
			expect(group.icon).toBeTruthy();
			expect(group.items.length).toBeGreaterThanOrEqual(1);
			for (const item of group.items) {
				expect(item.key).toBeTruthy();
				expect(item.label).toBeTruthy();
				expect(item.labelPlural).toBeTruthy();
			}
		}
	});

	it('has entities with columns and createForm', () => {
		const entityKeys = Object.keys(layout.entities);
		expect(entityKeys.length).toBeGreaterThanOrEqual(1);

		for (const [key, entity] of Object.entries(layout.entities)) {
			expect(entity.label).toBeTruthy();
			expect(entity.labelPlural).toBeTruthy();
			expect(entity.columns.length).toBeGreaterThanOrEqual(1);

			// At least one column should be primary
			const primaryCols = entity.columns.filter((c) => c.primary);
			expect(primaryCols.length).toBeGreaterThanOrEqual(1);

			// createForm must have at least one section with fields
			expect(entity.createForm.action).toBeTruthy();
			expect(entity.createForm.submitLabel).toBeTruthy();
			expect(entity.createForm.sections.length).toBeGreaterThanOrEqual(1);
			for (const section of entity.createForm.sections) {
				expect(section.label).toBeTruthy();
				expect(section.fields.length).toBeGreaterThanOrEqual(1);
			}
		}
	});

	it('has mock data for every entity', () => {
		for (const key of Object.keys(layout.entities)) {
			expect(layout.mockData[key]).toBeDefined();
			expect(layout.mockData[key].length).toBeGreaterThanOrEqual(1);
		}
	});

	it('mock data fields match entity columns', () => {
		for (const [key, entity] of Object.entries(layout.entities)) {
			const data = layout.mockData[key];
			if (!data?.length) continue;

			const row = data[0];
			for (const col of entity.columns) {
				expect(row).toHaveProperty(col.field);
			}
		}
	});

	it('has attention items with valid severity', () => {
		expect(layout.attention.length).toBeGreaterThanOrEqual(1);
		const validSeverities = ['critical', 'warning', 'info'];
		for (const item of layout.attention) {
			expect(item.message).toBeTruthy();
			expect(validSeverities).toContain(item.severity);
		}
	});

	it('has activity items with timestamps', () => {
		expect(layout.activity.length).toBeGreaterThanOrEqual(1);
		for (const item of layout.activity) {
			expect(item.message).toBeTruthy();
			expect(item.timestamp).toBeTruthy();
		}
	});

	it('sidebar entity keys reference existing entities or mock data', () => {
		const allSidebarKeys = layout.sidebar.flatMap((g) => g.items.map((i) => i.key));
		const entityKeys = new Set(Object.keys(layout.entities));
		const mockKeys = new Set(Object.keys(layout.mockData));

		// Not all sidebar items need entities (some are browse-only), but
		// every entity must appear in sidebar
		for (const key of entityKeys) {
			expect(allSidebarKeys).toContain(key);
		}
	});

	it('status filter values appear in mock data', () => {
		for (const [key, entity] of Object.entries(layout.entities)) {
			if (!entity.filters?.length || !entity.statusColors) continue;
			const data = layout.mockData[key];
			if (!data?.length) continue;

			// Only check entities with statusColors (status-driven filtering)
			const dataStatuses = new Set(data.map((r) => r.status).filter(Boolean));
			const overlap = entity.filters.filter((f) => dataStatuses.has(f));
			expect(overlap.length).toBeGreaterThanOrEqual(1);
		}
	});
});

describe('Cross-vertical uniqueness', () => {
	it('all verticals have unique names', () => {
		const names = verticals.map(([n]) => n);
		expect(new Set(names).size).toBe(names.length);
	});

	it('all verticals have unique labels', () => {
		const labels = verticals.map(([, v]) => v.label);
		expect(new Set(labels).size).toBe(labels.length);
	});
});
