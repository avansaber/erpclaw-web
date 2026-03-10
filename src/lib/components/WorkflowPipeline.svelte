<script lang="ts">
	import type { WorkflowDef } from '$lib/types';
	import { fly } from 'svelte/transition';

	let { workflow, index = 0 }: { workflow: WorkflowDef; index?: number } = $props();
</script>

<div
	class="rounded-xl border border-border bg-card p-4"
	in:fly={{ y: 12, delay: index * 100, duration: 300 }}
	role="region"
	aria-label="{workflow.label} pipeline"
>
	<div class="mb-3 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-lg" aria-hidden="true">{workflow.icon}</span>
			<span class="text-sm font-medium">{workflow.label}</span>
		</div>
		<button
			class="cursor-pointer rounded-md border border-border px-2.5 py-1 text-xs transition-colors hover:border-accent hover:text-accent"
		>
			{workflow.primaryAction}
		</button>
	</div>
	<!-- Horizontal scroll on mobile -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1">
		{#each workflow.steps as step, i}
			<div
				class="min-w-[80px] flex-1 rounded-lg border border-border p-2 text-center"
				class:border-l-3={!!step.count}
				style:border-left-color={step.count ? step.countColor : undefined}
			>
				<p class="text-xs text-muted">{step.label}</p>
				{#if step.count}
					<p class="text-sm font-bold" style:color={step.countColor}>{step.count}</p>
				{:else}
					<p class="text-sm text-muted">&mdash;</p>
				{/if}
			</div>
			{#if i < workflow.steps.length - 1}
				<span class="hidden text-xs text-muted sm:inline" aria-hidden="true">&rarr;</span>
			{/if}
		{/each}
	</div>
</div>
