import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import { currentVerticalKey, layout, verticals } from '$lib/stores';

describe('stores', () => {
	it('defaults to erpclaw vertical', () => {
		expect(get(currentVerticalKey)).toBe('erpclaw');
	});

	it('layout derives from currentVerticalKey', () => {
		const l = get(layout);
		expect(l.name).toBe('erpclaw');
		expect(l.label).toBe('ERPClaw');
	});

	it('has 3 registered verticals', () => {
		expect(Object.keys(verticals)).toEqual(['erpclaw', 'dental', 'property']);
	});

	it('switching vertical updates derived layout', () => {
		currentVerticalKey.set('dental');
		const l = get(layout);
		expect(l.name).toBe('dental');
		expect(l.label).toBe('Dental Practice');

		// Reset to default
		currentVerticalKey.set('erpclaw');
	});
});
