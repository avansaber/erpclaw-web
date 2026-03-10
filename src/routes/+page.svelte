<script lang="ts">
	import KPIGrid from '$lib/components/KPIGrid.svelte';
	import WorkflowPipeline from '$lib/components/WorkflowPipeline.svelte';
	import AttentionList from '$lib/components/AttentionList.svelte';
	import ActivityFeed from '$lib/components/ActivityFeed.svelte';
	import { layout } from '$lib/stores';
</script>

<div class="mx-auto max-w-6xl space-y-6">
	<div>
		<h1 class="text-lg font-semibold">Dashboard</h1>
		<p class="text-sm text-muted">{$layout.description}</p>
	</div>

	<KPIGrid items={$layout.kpis} />

	<div class="space-y-3">
		<h2 class="text-sm font-medium text-muted">Workflows</h2>
		{#each $layout.workflows as wf, i}
			<WorkflowPipeline workflow={wf} index={i} />
		{/each}
	</div>

	<!-- Attention + Activity side-by-side on desktop, stacked on mobile -->
	<div class="grid gap-6 lg:grid-cols-2">
		<AttentionList items={$layout.attention} />
		<ActivityFeed items={$layout.activity} />
	</div>
</div>
