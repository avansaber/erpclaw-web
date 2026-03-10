import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('UI.yaml v2 JSON Schema', () => {
	const schemaPath = resolve(__dirname, '../../schema/ui-yaml-v2.json');
	let schema: Record<string, unknown>;

	it('is valid JSON', () => {
		const raw = readFileSync(schemaPath, 'utf-8');
		schema = JSON.parse(raw);
		expect(schema).toBeDefined();
	});

	it('has correct $schema and $id', () => {
		const raw = readFileSync(schemaPath, 'utf-8');
		schema = JSON.parse(raw);
		expect(schema.$schema).toContain('json-schema.org');
		expect(schema.$id).toContain('erpclaw');
	});

	it('requires all top-level fields', () => {
		const raw = readFileSync(schemaPath, 'utf-8');
		schema = JSON.parse(raw);
		const required = schema.required as string[];
		expect(required).toContain('name');
		expect(required).toContain('label');
		expect(required).toContain('kpis');
		expect(required).toContain('workflows');
		expect(required).toContain('sidebar');
		expect(required).toContain('entities');
		expect(required).toContain('attention');
		expect(required).toContain('activity');
	});

	it('defines all component $defs', () => {
		const raw = readFileSync(schemaPath, 'utf-8');
		schema = JSON.parse(raw);
		const defs = schema.$defs as Record<string, unknown>;
		const expectedDefs = [
			'KPIItem', 'WorkflowStep', 'WorkflowDef',
			'SidebarItem', 'SidebarGroup',
			'ColumnDef', 'FormField', 'FormSection', 'FormSpec',
			'EntityDef', 'AttentionItem', 'ActivityItem',
			'DetailSection', 'RoleOverride'
		];
		for (const def of expectedDefs) {
			expect(defs).toHaveProperty(def);
		}
	});
});
