<script lang="ts">
	import type { SearchResult } from '$lib/types';
	import { layout } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';

	let { open = $bindable(false) }: { open?: boolean } = $props();

	let query = $state('');
	let selectedIndex = $state(0);
	let inputEl = $state<HTMLInputElement | null>(null);
	let listboxId = 'cmd-listbox';

	// Build search index from current layout
	let allResults = $derived.by(() => {
		const results: SearchResult[] = [];
		const l = $layout;

		// Dashboard
		results.push({
			type: 'page',
			label: 'Dashboard',
			description: l.description,
			href: '/',
			icon: '🏠'
		});

		// Entities from sidebar
		for (const group of l.sidebar) {
			for (const item of group.items) {
				results.push({
					type: 'entity',
					label: item.labelPlural,
					description: `Browse ${item.labelPlural.toLowerCase()}`,
					href: `/${item.key}`,
					icon: group.icon
				});
			}
		}

		// Create actions from entities
		for (const [key, def] of Object.entries(l.entities)) {
			results.push({
				type: 'action',
				label: `New ${def.label}`,
				description: def.createForm.action,
				href: `/${key}/new`,
				icon: '➕'
			});
		}

		return results;
	});

	let filtered = $derived(
		query.trim() === ''
			? allResults.slice(0, 8)
			: allResults.filter(
					(r) =>
						r.label.toLowerCase().includes(query.toLowerCase()) ||
						r.description?.toLowerCase().includes(query.toLowerCase())
				)
	);

	$effect(() => {
		if (open) {
			query = '';
			selectedIndex = 0;
			requestAnimationFrame(() => inputEl?.focus());
		}
	});

	// Reset selection when results change
	$effect(() => {
		if (filtered.length > 0 && selectedIndex >= filtered.length) {
			selectedIndex = 0;
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			selectedIndex = Math.min(selectedIndex + 1, filtered.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selectedIndex = Math.max(selectedIndex - 1, 0);
		} else if (e.key === 'Enter' && filtered[selectedIndex]) {
			e.preventDefault();
			navigate(filtered[selectedIndex]);
		} else if (e.key === 'Escape') {
			open = false;
		}
	}

	function navigate(result: SearchResult) {
		open = false;
		goto(result.href);
	}

	const typeIcons: Record<string, string> = {
		entity: '📋',
		action: '➕',
		page: '📊'
	};
</script>

{#if open}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[15vh]"
		onclick={() => (open = false)}
		onkeydown={handleKeydown}
		transition:fly={{ duration: 150 }}
	>
		<!-- Panel -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<div
			class="w-full max-w-lg overflow-hidden rounded-xl border border-border bg-surface shadow-2xl"
			onclick={(e) => e.stopPropagation()}
			role="dialog"
			aria-label="Command palette"
			transition:fly={{ y: -20, duration: 200 }}
		>
			<div class="flex items-center gap-3 border-b border-border p-4">
				<span class="text-muted" aria-hidden="true">🔍</span>
				<input
					bind:this={inputEl}
					bind:value={query}
					onkeydown={handleKeydown}
					placeholder="Search entities, actions, pages..."
					class="flex-1 bg-transparent text-sm text-text outline-none placeholder:text-muted"
					role="combobox"
					aria-label="Search"
					aria-expanded="true"
					aria-controls={listboxId}
					aria-activedescendant={filtered[selectedIndex] ? `cmd-option-${selectedIndex}` : undefined}
					autocomplete="off"
				/>
				<kbd class="rounded border border-border px-1.5 py-0.5 text-[10px] text-muted">ESC</kbd>
			</div>

			<ul id={listboxId} class="max-h-80 overflow-y-auto p-2" role="listbox">
				{#each filtered as result, i}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<li
						id="cmd-option-{i}"
						role="option"
						aria-selected={i === selectedIndex}
						class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors"
						class:bg-card={i === selectedIndex}
						onmouseenter={() => (selectedIndex = i)}
						onclick={() => navigate(result)}
					>
						<span class="text-base" aria-hidden="true">{result.icon ?? typeIcons[result.type]}</span>
						<div class="flex-1">
							<p class="font-medium">{result.label}</p>
							{#if result.description}
								<p class="text-xs text-muted">{result.description}</p>
							{/if}
						</div>
						<span
							class="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted"
						>
							{result.type}
						</span>
					</li>
				{:else}
					<li class="px-3 py-6 text-center text-sm text-muted">No results for "{query}"</li>
				{/each}
			</ul>

			<div class="flex gap-4 border-t border-border px-4 py-2 text-[10px] text-muted">
				<span>↑↓ Navigate</span>
				<span>↵ Open</span>
				<span>ESC Close</span>
			</div>
		</div>
	</div>
{/if}
