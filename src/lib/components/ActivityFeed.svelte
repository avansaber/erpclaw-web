<script lang="ts">
	import type { ActivityItem } from '$lib/types';
	import { fly } from 'svelte/transition';

	let { items, limit = 5 }: { items: ActivityItem[]; limit?: number } = $props();

	let visible = $derived(items.slice(0, limit));
</script>

{#if items.length > 0}
	<div in:fly={{ y: 8, duration: 200 }}>
		<h3 class="mb-2 text-sm font-medium text-muted">Recent Activity</h3>
		<div class="space-y-1">
			{#each visible as item, i}
				<svelte:element
					this={item.href ? 'a' : 'div'}
					href={item.href}
					class="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-card"
					in:fly={{ y: 4, delay: i * 40, duration: 200 }}
				>
					{#if item.icon}
						<span class="text-sm" aria-hidden="true">{item.icon}</span>
					{:else}
						<span class="text-sm text-muted" aria-hidden="true">•</span>
					{/if}
					<span class="flex-1 text-sm">{item.message}</span>
					<span class="text-xs text-muted">{item.timestamp}</span>
				</svelte:element>
			{/each}
		</div>
	</div>
{/if}
