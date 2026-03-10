<script lang="ts">
	import type { AttentionItem } from '$lib/types';
	import { fly } from 'svelte/transition';

	let { items }: { items: AttentionItem[] } = $props();

	const severityConfig = {
		critical: { icon: '🔴', bg: 'var(--color-red)', label: 'Critical' },
		warning: { icon: '⚠️', bg: 'var(--color-amber)', label: 'Warning' },
		info: { icon: 'ℹ️', bg: 'var(--color-accent)', label: 'Info' }
	};
</script>

{#if items.length > 0}
	<div in:fly={{ y: 8, duration: 200 }}>
		<h3 class="mb-2 text-sm font-medium text-muted">Needs Attention</h3>
		<div class="space-y-2">
			{#each items as item, i}
				{@const config = severityConfig[item.severity]}
				<svelte:element
					this={item.href ? 'a' : 'div'}
					href={item.href}
					class="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-card"
					style:border-left="3px solid {config.bg}"
					role="alert"
					in:fly={{ y: 6, delay: i * 60, duration: 200 }}
				>
					<span class="text-sm" aria-hidden="true">{config.icon}</span>
					<span class="flex-1 text-sm">{item.message}</span>
					{#if item.href}
						<span class="text-xs text-muted">→</span>
					{/if}
				</svelte:element>
			{/each}
		</div>
	</div>
{/if}
