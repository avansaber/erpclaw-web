<script lang="ts">
	import { toasts, removeToast } from '$lib/toast';
	import { fly } from 'svelte/transition';

	const icons: Record<string, string> = { success: '\u2713', error: '\u2717', info: '\u24D8' };

	function toastClasses(type: string): string {
		if (type === 'success') return 'border-emerald bg-emerald/10 text-emerald';
		if (type === 'error') return 'border-red bg-red/10 text-red';
		return 'border-accent bg-accent/10 text-accent';
	}
</script>

{#if $toasts.length > 0}
	<div class="fixed bottom-4 right-4 z-[200] flex flex-col gap-2" aria-live="assertive">
		{#each $toasts as toast (toast.id)}
			<div
				class="flex items-center gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg backdrop-blur-sm {toastClasses(toast.type)}"
				role="alert"
				transition:fly={{ x: 100, duration: 200 }}
			>
				<span>{icons[toast.type]}</span>
				<span class="flex-1">{toast.message}</span>
				<button
					class="cursor-pointer text-xs opacity-60 hover:opacity-100"
					onclick={() => removeToast(toast.id)}
					aria-label="Dismiss"
				>
					x
				</button>
			</div>
		{/each}
	</div>
{/if}
