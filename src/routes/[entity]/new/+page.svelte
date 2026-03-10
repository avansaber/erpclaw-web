<script lang="ts">
	import FormRenderer from '$lib/components/FormRenderer.svelte';
	import { layout } from '$lib/stores';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { executeAction, skillForAction } from '$lib/api';
	import { addToast } from '$lib/toast';

	let entityKey = $derived($page.params.entity ?? '');
	let entityDef = $derived(entityKey ? $layout.entities[entityKey] : undefined);
	let loading = $state(false);

	async function handleSubmit(data: Record<string, unknown>) {
		if (!entityDef) return;

		const action = entityDef.createForm.action;
		const skill = skillForAction(action);

		loading = true;
		const result = await executeAction(skill, action, data);
		loading = false;

		if (!result.error) {
			addToast(`${entityDef.label} created successfully`, 'success');
			goto(`/${entityKey}`);
		}
		// Error toast is shown by executeAction
	}
</script>

{#if entityDef}
	<div class="mx-auto max-w-6xl">
		<div class="mb-6">
			<div class="flex items-center gap-2 text-sm text-muted">
				<a href="/{entityKey}" class="hover:text-accent">{entityDef.labelPlural}</a>
				<span>/</span>
				<span>New {entityDef.label}</span>
			</div>
			<h1 class="mt-1 text-lg font-semibold">New {entityDef.label}</h1>
		</div>

		<FormRenderer spec={entityDef.createForm} onSubmit={handleSubmit} {loading} />
	</div>
{:else}
	<div class="flex flex-col items-center justify-center py-20 text-center">
		<p class="text-4xl">&#x1F4ED;</p>
		<p class="mt-3 text-lg font-medium">No form found</p>
		<a href="/" class="mt-4 text-sm text-accent hover:underline">&larr; Back to Dashboard</a>
	</div>
{/if}
