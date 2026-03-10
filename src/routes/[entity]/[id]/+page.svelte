<script lang="ts">
	import EntityDetail from '$lib/components/EntityDetail.svelte';
	import { layout } from '$lib/stores';
	import { page } from '$app/stores';

	let entityKey = $derived($page.params.entity ?? '');
	let id = $derived($page.params.id ?? '0');
	let entityDef = $derived(entityKey ? $layout.entities[entityKey] : undefined);
	let entityData = $derived(entityKey ? ($layout.mockData[entityKey] ?? []) : []);

	// Find the record by index (mock data has no real IDs)
	let record = $derived(entityData[Number(id)] ?? entityData[0]);
</script>

{#if entityDef && record}
	<div class="mx-auto max-w-4xl">
		<EntityDetail
			record={record}
			entityDef={entityDef}
			panel={false}
		/>
	</div>
{:else}
	<div class="flex flex-col items-center justify-center py-20 text-center">
		<p class="text-4xl">📭</p>
		<p class="mt-3 text-lg font-medium">Record not found</p>
		<p class="mt-1 text-sm text-muted">Could not find this {entityKey} record.</p>
		<a href="/{entityKey}" class="mt-4 text-sm text-accent hover:underline">← Back to list</a>
	</div>
{/if}
