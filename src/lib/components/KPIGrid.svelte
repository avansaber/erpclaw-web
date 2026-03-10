<script lang="ts">
	import type { KPIItem } from '$lib/types';
	import { fly } from 'svelte/transition';

	let { items }: { items: KPIItem[] } = $props();
</script>

<div class="grid grid-cols-2 gap-3 lg:grid-cols-4" role="region" aria-label="Key metrics">
	{#each items as item, i}
		<div
			class="rounded-xl border border-border bg-card p-4 transition-all hover:border-accent/40"
			in:fly={{ y: 12, delay: i * 80, duration: 300 }}
		>
			<p class="text-xs text-muted">{item.label}</p>
			<p class="mt-1 text-xl font-bold sm:text-2xl" style:color={item.color}>{item.value}</p>
			<p class="mt-0.5 text-xs text-muted">{item.sub}</p>
		</div>
	{/each}
</div>
