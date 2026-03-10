<script lang="ts">
	import type { EntityDef } from '$lib/types';
	import { fly } from 'svelte/transition';

	let {
		record,
		entityDef,
		panel = false,
		onClose,
		onAction,
		actionLoading
	}: {
		record: Record<string, unknown>;
		entityDef: EntityDef;
		panel?: boolean;
		onClose?: () => void;
		onAction?: (action: string) => void;
		actionLoading?: string | null;
	} = $props();

	function formatValue(value: unknown, col?: { format?: string }): string {
		if (value == null || value === '') return '—';
		const v = String(value);
		if (col?.format === 'currency') return `$${Number(v).toLocaleString()}`;
		return v;
	}

	function statusColor(value: unknown): string | undefined {
		return entityDef.statusColors?.[String(value)];
	}

	function actionLabel(action: string): string {
		return action.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
	}

	// Derive display fields from columns
	let primaryField = $derived(entityDef.columns.find((c) => c.primary)?.field ?? entityDef.columns[0]?.field);
	let statusField = $derived(entityDef.columns.find((c) => c.format === 'status_badge'));
</script>

<div
	class="flex h-full flex-col overflow-y-auto {panel ? 'border-l border-border bg-surface' : ''}"
	role="complementary"
	aria-label="{entityDef.label} detail"
	in:fly={{ x: panel ? 300 : 0, y: panel ? 0 : 8, duration: 250 }}
>
	<!-- Header -->
	<div class="flex items-center justify-between border-b border-border p-4">
		<div class="flex-1">
			<p class="text-xs text-muted">{entityDef.label}</p>
			<h2 class="text-lg font-semibold">{formatValue(record[primaryField])}</h2>
			{#if statusField}
				<span
					class="mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium"
					style:background="{statusColor(record[statusField.field])}20"
					style:color={statusColor(record[statusField.field])}
				>
					{record[statusField.field]}
				</span>
			{/if}
		</div>
		<div class="flex items-center gap-2">
			{#if !panel}
				<a
					href="/{entityDef.label.toLowerCase()}"
					class="rounded-md border border-border px-2.5 py-1 text-xs text-muted hover:text-text"
				>
					&larr; Back
				</a>
			{/if}
			{#if panel && onClose}
				<button
					class="cursor-pointer rounded-md border border-border px-2.5 py-1 text-xs text-muted hover:text-text"
					onclick={onClose}
					aria-label="Close detail panel"
				>
					&#10005;
				</button>
			{/if}
		</div>
	</div>

	<!-- Actions -->
	{#if entityDef.actions?.length}
		<div class="flex flex-wrap gap-2 border-b border-border p-4">
			{#each entityDef.actions as action}
				<button
					class="cursor-pointer rounded-md border border-border px-3 py-1.5 text-xs transition-colors hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
					disabled={actionLoading === action}
					onclick={() => onAction?.(action)}
				>
					{#if actionLoading === action}
						Running...
					{:else}
						{actionLabel(action)}
					{/if}
				</button>
			{/each}
		</div>
	{/if}

	<!-- Field sections -->
	<div class="flex-1 p-4">
		{#if entityDef.detailSections}
			{#each entityDef.detailSections as section}
				<div class="mb-4 rounded-xl border border-border p-4">
					<p class="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
						{section.label}
					</p>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						{#each section.fields as field}
							{@const col = entityDef.columns.find((c) => c.field === field)}
							<div>
								<p class="text-xs text-muted">{col?.label ?? field}</p>
								<p class="text-sm font-medium">{formatValue(record[field], col)}</p>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		{:else}
			<!-- Auto-generate from columns -->
			<div class="rounded-xl border border-border p-4">
				<p class="mb-3 text-xs font-medium uppercase tracking-wider text-muted">Details</p>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					{#each entityDef.columns as col}
						{#if col.format !== 'status_badge'}
							<div>
								<p class="text-xs text-muted">{col.label}</p>
								<p class="text-sm font-medium">{formatValue(record[col.field], col)}</p>
							</div>
						{/if}
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
