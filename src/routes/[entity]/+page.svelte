<script lang="ts">
	import DataTable from '$lib/components/DataTable.svelte';
	import EntityDetail from '$lib/components/EntityDetail.svelte';
	import { layout } from '$lib/stores';
	import { page } from '$app/stores';
	import { fly } from 'svelte/transition';
	import { fetchEntityData, executeAction, skillForAction } from '$lib/api';
	import type { FetchResult } from '$lib/api';
	import { addToast } from '$lib/toast';
	import { isLoading as authLoading, isAuthenticated } from '$lib/auth';
	import { onWSEvent } from '$lib/websocket';
	import { onDestroy } from 'svelte';

	let entityKey = $derived($page.params.entity ?? '');
	let entityDef = $derived(entityKey ? $layout.entities[entityKey] : undefined);
	let mockData = $derived(entityKey ? ($layout.mockData[entityKey] ?? []) : []);

	let liveData = $state<Record<string, unknown>[] | null>(null);
	let loadingData = $state(false);
	let loadingMore = $state(false);
	let totalCount = $state(0);
	let hasMore = $state(false);
	let selectedRow = $state<Record<string, unknown> | null>(null);
	let actionLoading = $state<string | null>(null);

	// Use live data if available, otherwise mock
	let entityData = $derived(liveData ?? mockData);

	// Fetch live data when entity changes AND auth is fully ready
	// (Must wait for auth.refresh() in root layout to complete — both loading=false AND user set)
	$effect(() => {
		if (entityKey && !$authLoading && $isAuthenticated) {
			selectedRow = null;
			liveData = null; // Clear stale data so DataTable unmounts during load
			loadLiveData();
		}
	});

	// Auto-refresh when WebSocket notifies of data changes
	const unsubWS = onWSEvent('data_changed', (data) => {
		const changedEntity = String(data.entity ?? '').replace(/-/g, '_');
		if (changedEntity === entityKey || changedEntity.includes(entityKey)) {
			loadLiveData();
		}
	});
	onDestroy(unsubWS);

	async function loadLiveData() {
		if (!entityKey) return;
		loadingData = true;
		// Fetch up to 200 initially so client-side filters work on the full dataset.
		// Load More handles any overflow beyond 200.
		const result = await fetchEntityData('erpclaw', entityKey, { limit: 200 });
		if (result) {
			liveData = result.rows;
			totalCount = result.totalCount;
			hasMore = result.hasMore;
		} else {
			liveData = null; // Fall back to mock
			totalCount = 0;
			hasMore = false;
		}
		loadingData = false;
	}

	async function handleLoadMore() {
		if (!entityKey || !liveData) return;
		loadingMore = true;
		const result = await fetchEntityData('erpclaw', entityKey, { offset: liveData.length });
		if (result) {
			liveData = [...liveData, ...result.rows];
			totalCount = result.totalCount;
			hasMore = result.hasMore;
		}
		loadingMore = false;
	}

	function handleRowClick(row: Record<string, unknown>) {
		selectedRow = row === selectedRow ? null : row;
	}

	async function handleAction(action: string) {
		if (!selectedRow || !entityDef) return;

		const skill = skillForAction(action);
		actionLoading = action;

		// Build params with the correct param name for this entity.
		// Backend expects e.g. --sales-order-id, --purchase-order-id, --sales-invoice-id
		const params: Record<string, unknown> = {};

		// Use _id (raw UUID) if available from live data, otherwise fall back to id
		const rowId = selectedRow._id ?? selectedRow.id;
		if (rowId) {
			// Convert entity key to param name: sales_order → sales_order_id
			const paramKey = `${entityKey}_id`;
			params[paramKey] = rowId;
		}

		const result = await executeAction(skill, action, params);
		actionLoading = null;

		if (!result.error) {
			const label = action.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
			addToast(`${label} completed`, 'success');
			// Refresh data
			await loadLiveData();
		}
	}
</script>

{#if entityDef}
	<div class="flex h-full gap-0">
		<!-- List panel -->
		<div class="flex-1 overflow-y-auto {selectedRow ? 'hidden md:block' : ''}" class:md:pr-0={!selectedRow}>
			<div class="mx-auto max-w-6xl space-y-4">
				<div class="flex items-center justify-between">
					<div>
						<h1 class="text-lg font-semibold">{entityDef.labelPlural}</h1>
						<p class="text-sm text-muted">
							{#if loadingData}
								Loading...
							{:else}
								{totalCount || entityData.length} {(totalCount || entityData.length) === 1 ? 'record' : 'records'}
								{#if liveData}<span class="text-emerald">(live)</span>{/if}
							{/if}
						</p>
					</div>
					<a
						href="/{entityKey}/new"
						class="rounded-lg px-4 py-2 text-sm font-medium text-white transition-all hover:brightness-110"
						style:background="var(--color-accent)"
					>
						+ New {entityDef.label}
					</a>
				</div>

				{#if entityData.length > 0}
					{#key entityKey}
					<DataTable
						columns={entityDef.columns}
						data={entityData}
						filters={entityDef.filters}
						filterField={entityDef.filterField ?? 'status'}
						statusColors={entityDef.statusColors ?? {}}
						onRowClick={handleRowClick}
						selectedRow={selectedRow}
						{totalCount}
						{hasMore}
						{loadingMore}
						onLoadMore={handleLoadMore}
					/>
					{/key}
				{:else if !loadingData}
					<div class="flex flex-col items-center justify-center rounded-xl border border-border py-16 text-center">
						<p class="text-4xl">&#x1F4ED;</p>
						<p class="mt-3 text-lg font-medium">No {entityDef.labelPlural.toLowerCase()} yet</p>
						<p class="mt-1 text-sm text-muted">Create your first {entityDef.label.toLowerCase()} to get started.</p>
						<a
							href="/{entityKey}/new"
							class="mt-4 inline-block rounded-lg px-4 py-2 text-sm font-medium text-white transition-all hover:brightness-110"
							style:background="var(--color-accent)"
						>
							+ New {entityDef.label}
						</a>
					</div>
				{/if}
			</div>
		</div>

		<!-- Detail side panel (SAP Fiori pattern) -->
		{#if selectedRow && entityDef}
			<div
				class="w-full border-l border-border md:w-96 lg:w-[420px]"
				transition:fly={{ x: 300, duration: 250 }}
			>
				<EntityDetail
					record={selectedRow}
					entityDef={entityDef}
					panel={true}
					onClose={() => (selectedRow = null)}
					onAction={handleAction}
					{actionLoading}
				/>
			</div>
		{/if}
	</div>
{:else}
	<div class="flex flex-col items-center justify-center py-20 text-center">
		<p class="text-4xl">&#x1F4ED;</p>
		<p class="mt-3 text-lg font-medium">No entity found</p>
		<p class="mt-1 text-sm text-muted">"{entityKey}" is not defined in the current layout.</p>
		<a href="/" class="mt-4 text-sm text-accent hover:underline">&larr; Back to Dashboard</a>
	</div>
{/if}
