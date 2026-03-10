<script lang="ts">
	import type { ChatMessage } from '$lib/types';
	import { layout } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';

	let { open = $bindable(false) }: { open?: boolean } = $props();

	let messages = $state<ChatMessage[]>([
		{ role: 'assistant', content: "Hi! I can help you navigate, create records, or find information. Try asking me something." }
	]);
	let input = $state('');
	let inputEl = $state<HTMLInputElement | null>(null);
	let messagesEl = $state<HTMLDivElement | null>(null);

	$effect(() => {
		if (open) requestAnimationFrame(() => inputEl?.focus());
	});

	function scrollToBottom() {
		requestAnimationFrame(() => {
			if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
		});
	}

	function handleSend() {
		const q = input.trim();
		if (!q) return;

		messages.push({ role: 'user', content: q });
		input = '';
		scrollToBottom();

		// Mock AI responses based on keywords
		setTimeout(() => {
			const lower = q.toLowerCase();
			const l = $layout;
			let response = "I'm not sure about that. Try asking about specific entities like customers, invoices, or patients.";

			// Check for entity navigation
			for (const group of l.sidebar) {
				for (const item of group.items) {
					if (lower.includes(item.label.toLowerCase()) || lower.includes(item.labelPlural.toLowerCase())) {
						if (lower.includes('new') || lower.includes('create') || lower.includes('add')) {
							response = `Opening the new ${item.label} form...`;
							setTimeout(() => goto(`/${item.key}/new`), 500);
						} else {
							response = `Opening ${item.labelPlural}...`;
							setTimeout(() => goto(`/${item.key}`), 500);
						}
						break;
					}
				}
			}

			if (lower.includes('dashboard') || lower.includes('home')) {
				response = 'Taking you to the dashboard...';
				setTimeout(() => goto('/'), 500);
			} else if (lower.includes('overdue') || lower.includes('attention')) {
				response = `You have ${l.attention.length} items needing attention. Check the dashboard for details.`;
			} else if (lower.includes('help')) {
				response = 'I can help you:\n• Navigate: "show me customers"\n• Create: "new invoice"\n• Search: "find overdue invoices"\n• Go home: "dashboard"';
			}

			messages.push({ role: 'assistant', content: response });
			scrollToBottom();
		}, 400);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		} else if (e.key === 'Escape') {
			open = false;
		}
	}
</script>

{#if open}
	<aside
		class="flex h-full w-80 flex-col border-l border-border bg-surface"
		role="complementary"
		aria-label="Chat assistant"
		transition:fly={{ x: 320, duration: 200 }}
	>
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-border p-3">
			<div class="flex items-center gap-2">
				<span class="text-sm">💬</span>
				<span class="text-sm font-medium">Assistant</span>
			</div>
			<button
				class="cursor-pointer rounded-md p-1 text-xs text-muted hover:text-text"
				onclick={() => (open = false)}
				aria-label="Close chat"
			>
				✕
			</button>
		</div>

		<!-- Messages -->
		<div bind:this={messagesEl} class="flex-1 space-y-3 overflow-y-auto p-3">
			{#each messages as msg}
				<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
					<div
						class="max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-line {msg.role === 'user'
							? 'bg-accent/20 text-text'
							: 'bg-card text-text'}"
					>
						{msg.content}
					</div>
				</div>
			{/each}
		</div>

		<!-- Input -->
		<div class="border-t border-border p-3">
			<div class="flex items-center gap-2">
				<input
					bind:this={inputEl}
					bind:value={input}
					onkeydown={handleKeydown}
					placeholder="Ask anything..."
					class="flex-1 rounded-lg border border-border bg-bg p-2 text-sm text-text outline-none placeholder:text-muted focus:border-accent"
					aria-label="Chat message"
				/>
				<button
					class="cursor-pointer rounded-lg bg-accent px-3 py-2 text-sm text-white transition-all hover:brightness-110"
					onclick={handleSend}
					aria-label="Send message"
				>
					↑
				</button>
			</div>
		</div>
	</aside>
{/if}
