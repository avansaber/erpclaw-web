<script lang="ts">
	import type { ColumnDef } from '$lib/types';
	import { fly } from 'svelte/transition';

	let {
		columns,
		data,
		filters = [],
		filterField = 'status',
		statusColors = {},
		onRowClick,
		selectedRow = null
	}: {
		columns: ColumnDef[];
		data: Record<string, unknown>[];
		filters?: string[];
		filterField?: string;
		statusColors?: Record<string, string>;
		onRowClick?: (row: Record<string, unknown>) => void;
		selectedRow?: Record<string, unknown> | null;
	} = $props();

	let activeFilter = $state('All');
	let focusedRowIndex = $state(-1);

	let filtered = $derived(
		activeFilter === 'All'
			? data
			: data.filter((r) => r[filterField] === activeFilter)
	);

	function formatCell(value: unknown, col: ColumnDef): string {
		if (value == null) return '—';
		const v = String(value);
		if (col.format === 'currency') return `$${Number(v).toLocaleString()}`;
		if (col.format === 'date') return v;
		return v;
	}

	function statusColor(value: unknown): string | undefined {
		return statusColors[String(value)];
	}

	function isSelected(row: Record<string, unknown>): boolean {
		if (!selectedRow) return false;
		return row === selectedRow;
	}

	function handleTableKeydown(e: KeyboardEvent) {
		if (filtered.length === 0) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			focusedRowIndex = Math.min(focusedRowIndex + 1, filtered.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			focusedRowIndex = Math.max(focusedRowIndex - 1, 0);
		} else if (e.key === 'Enter' && focusedRowIndex >= 0) {
			e.preventDefault();
			onRowClick?.(filtered[focusedRowIndex]);
		} else if (e.key === 'Escape') {
			focusedRowIndex = -1;
		}
	}

	function exportCSV() {
		const headers = columns.map((c) => c.label).join(',');
		const rows = filtered.map((row) =>
			columns.map((c) => {
				const val = row[c.field];
				const s = val == null ? '' : String(val);
				return s.includes(',') ? `"${s}"` : s;
			}).join(',')
		);
		const csv = [headers, ...rows].join('\n');
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'export.csv';
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<div in:fly={{ y: 8, duration: 200 }}>
	<!-- Filters + export row -->
	<div class="mb-3 flex items-center justify-between gap-2">
		{#if filters.length > 0}
			<div class="flex flex-wrap gap-2" role="tablist" aria-label="Status filters">
				{#each ['All', ...filters] as f}
					<button
						role="tab"
						aria-selected={activeFilter === f}
						class="cursor-pointer rounded-full border px-2.5 py-1 text-xs transition-colors"
						class:border-accent={activeFilter === f}
						class:text-accent={activeFilter === f}
						class:border-border={activeFilter !== f}
						class:text-muted={activeFilter !== f}
						onclick={() => (activeFilter = f)}
					>
						{f}
					</button>
				{/each}
			</div>
		{:else}
			<div></div>
		{/if}
		<button
			class="cursor-pointer rounded-md border border-border px-2.5 py-1 text-xs text-muted transition-colors hover:border-accent hover:text-accent"
			onclick={exportCSV}
			aria-label="Export as CSV"
		>
			↓ CSV
		</button>
	</div>

	<!-- Table -->
	<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
	<div
		class="overflow-x-auto rounded-xl border border-border"
		role="grid"
		aria-label="Data table"
		tabindex="0"
		onkeydown={handleTableKeydown}
	>
		<table class="w-full text-sm">
			<caption class="sr-only">Data table with {filtered.length} rows</caption>
			<thead class="sticky top-0 z-10">
				<tr class="border-b border-border bg-surface">
					{#each columns as col}
						<th
							scope="col"
							class="p-3 text-left text-xs font-medium text-muted"
							class:text-right={col.align === 'right'}
							style:width={col.width ? `${col.width}px` : undefined}
						>
							{col.label}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each filtered as row, i}
					<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
					<tr
						class="cursor-pointer border-b border-border transition-colors last:border-b-0"
						class:bg-card={isSelected(row) || focusedRowIndex === i}
						class:hover:bg-card={!isSelected(row)}
						onclick={() => onRowClick?.(row)}
						onkeydown={(e) => e.key === 'Enter' && onRowClick?.(row)}
						in:fly={{ y: 4, delay: i * 30, duration: 200 }}
						role="row"
						aria-selected={isSelected(row)}
					>
						{#each columns as col}
							<td
								class="p-3"
								class:text-right={col.align === 'right'}
								class:font-medium={col.primary}
								class:text-accent={col.primary && isSelected(row)}
							>
								{#if col.format === 'status_badge'}
									<span
										class="rounded-full px-2 py-0.5 text-xs font-medium"
										style:background="{statusColor(row[col.field])}20"
										style:color={statusColor(row[col.field])}
									>
										{row[col.field]}
									</span>
								{:else}
									{formatCell(row[col.field], col)}
								{/if}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<!-- Record count -->
	<p class="mt-2 text-xs text-muted" aria-live="polite">
		Showing {filtered.length} of {data.length} records
		{#if activeFilter !== 'All'} · Filtered: {activeFilter}{/if}
	</p>
</div>

<style>
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		border: 0;
	}
</style>
