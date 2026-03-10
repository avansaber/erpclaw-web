<script lang="ts">
	import type { SidebarGroup } from '$lib/types';
	import { currentVerticalKey, verticals as verticalsStore, layout } from '$lib/stores';
	import { slide } from 'svelte/transition';
	import { goto } from '$app/navigation';

	let { groups, activeEntity = '' }: { groups: SidebarGroup[]; activeEntity?: string } = $props();

	let expandedGroups = $state<Record<string, boolean>>(
		Object.fromEntries(groups.map((g) => [g.label, g.expanded]))
	);

	let showVerticalPicker = $state(false);

	function toggleGroup(label: string) {
		expandedGroups[label] = !expandedGroups[label];
	}

	function switchVertical(key: string) {
		currentVerticalKey.set(key);
		showVerticalPicker = false;
		goto('/');
	}

	$effect(() => {
		expandedGroups = Object.fromEntries(groups.map((g) => [g.label, g.expanded]));
	});
</script>

<aside class="flex h-full w-56 flex-col border-r border-border bg-surface" aria-label="Navigation">
	<!-- Vertical Switcher -->
	<div class="border-b border-border p-3">
		<button
			class="flex w-full cursor-pointer items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm transition-colors hover:border-accent"
			onclick={() => (showVerticalPicker = !showVerticalPicker)}
			aria-expanded={showVerticalPicker}
			aria-haspopup="listbox"
		>
			<span class="text-lg" aria-hidden="true">{$layout.icon}</span>
			<span class="flex-1 text-left font-medium">{$layout.label}</span>
			<span class="text-xs text-muted" aria-hidden="true">{showVerticalPicker ? '▲' : '▼'}</span>
		</button>

		{#if showVerticalPicker}
			<div class="mt-2 space-y-1" role="listbox" aria-label="Verticals" transition:slide={{ duration: 150 }}>
				{#each Object.entries($verticalsStore) as [key, v]}
					<button
						role="option"
						aria-selected={$currentVerticalKey === key}
						class="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors hover:bg-card"
						class:bg-card={$currentVerticalKey === key}
						onclick={() => switchVertical(key)}
					>
						<span aria-hidden="true">{v.icon}</span>
						<span>{v.label}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Navigation Groups -->
	<nav class="flex-1 overflow-y-auto p-2" aria-label="Sidebar navigation">
		{#each groups as group}
			<div class="mb-1">
				<button
					class="flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium uppercase tracking-wider text-muted transition-colors hover:text-text"
					onclick={() => toggleGroup(group.label)}
					aria-expanded={!!expandedGroups[group.label]}
				>
					<span aria-hidden="true">{group.icon}</span>
					<span class="flex-1 text-left">{group.label}</span>
					<span class="text-[10px]" aria-hidden="true">{expandedGroups[group.label] ? '▾' : '▸'}</span>
				</button>

				{#if expandedGroups[group.label]}
					<div transition:slide={{ duration: 150 }}>
						{#each group.items as item}
							<a
								href="/{item.key}"
								class="block rounded-md px-4 py-1.5 text-sm transition-colors hover:bg-card"
								class:bg-card={activeEntity === item.key}
								class:text-accent={activeEntity === item.key}
								class:text-muted={activeEntity !== item.key}
								aria-current={activeEntity === item.key ? 'page' : undefined}
							>
								{item.labelPlural}
							</a>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</nav>

	<!-- Dashboard link at bottom -->
	<div class="border-t border-border p-2">
		<a
			href="/"
			class="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted transition-colors hover:bg-card hover:text-text"
			aria-current={activeEntity === '' ? 'page' : undefined}
		>
			<span aria-hidden="true">🏠</span>
			<span>Dashboard</span>
		</a>
	</div>
</aside>
