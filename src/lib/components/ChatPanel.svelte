<script lang="ts">
	import type { ChatMessage } from '$lib/types';
	import { auth } from '$lib/auth';
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';
	import { executeAction } from '$lib/api';
	import { addToast } from '$lib/toast';

	let { open = $bindable(false) }: { open?: boolean } = $props();

	let messages = $state<ChatMessage[]>([
		{
			role: 'assistant',
			content:
				"Hi! I can help you navigate, create records, query data, or execute actions. Try asking me something.",
			suggestions: [
				'Show me customers',
				'How many overdue invoices?',
				'New sales order',
				'Total revenue this month'
			]
		}
	]);
	let input = $state('');
	let inputEl = $state<HTMLInputElement | null>(null);
	let messagesEl = $state<HTMLDivElement | null>(null);
	let sending = $state(false);

	$effect(() => {
		if (open) requestAnimationFrame(() => inputEl?.focus());
	});

	function scrollToBottom() {
		requestAnimationFrame(() => {
			if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
		});
	}

	async function handleSend(text?: string) {
		const q = (text ?? input).trim();
		if (!q || sending) return;

		messages.push({ role: 'user', content: q });
		input = '';
		sending = true;
		scrollToBottom();

		try {
			const res = await auth.apiFetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: q, vertical: 'erpclaw' })
			});

			const data = await res.json();

			const msg: ChatMessage = {
				role: 'assistant',
				content: data.message ?? 'Something went wrong.',
				href: data.href,
				action: data.action,
				suggestions: data.suggestions
			};
			messages.push(msg);
			scrollToBottom();

			// Auto-navigate after a short delay
			if (data.type === 'navigate' && data.href) {
				setTimeout(() => goto(data.href), 600);
			}
		} catch {
			messages.push({
				role: 'assistant',
				content: "Sorry, I couldn't reach the server. Try again in a moment."
			});
			scrollToBottom();
		} finally {
			sending = false;
		}
	}

	async function handleActionConfirm(action: {
		skill: string;
		action: string;
		params: Record<string, unknown>;
	}) {
		messages.push({ role: 'user', content: 'Yes, go ahead.' });
		sending = true;
		scrollToBottom();

		const result = await executeAction(action.skill, action.action, action.params);

		if (result.error) {
			messages.push({ role: 'assistant', content: `Action failed: ${result.error}` });
		} else {
			const label = action.action
				.replace(/-/g, ' ')
				.replace(/\b\w/g, (c) => c.toUpperCase());
			messages.push({
				role: 'assistant',
				content: `Done! ${label} completed successfully.`
			});
			addToast(`${label} completed`, 'success');
		}

		sending = false;
		scrollToBottom();
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
		class="flex h-full w-full flex-col border-l border-border bg-surface sm:w-80"
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
						class="max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-line {msg.role ===
						'user'
							? 'bg-accent/20 text-text'
							: 'bg-card text-text'}"
					>
						<!-- Render markdown bold -->
						{@html msg.content
							.replace(/&/g, '&amp;')
							.replace(/</g, '&lt;')
							.replace(/>/g, '&gt;')
							.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
							.replace(/\n/g, '<br>')}
					</div>
				</div>

				<!-- Action confirmation button -->
				{#if msg.role === 'assistant' && msg.action}
					<div class="flex justify-start">
						<button
							class="cursor-pointer rounded-lg border border-accent px-3 py-1.5 text-xs text-accent transition-colors hover:bg-accent/10"
							onclick={() => msg.action && handleActionConfirm(msg.action)}
							disabled={sending}
						>
							{sending ? 'Executing...' : 'Confirm & Execute'}
						</button>
					</div>
				{/if}

				<!-- Navigation link -->
				{#if msg.role === 'assistant' && msg.href && !msg.action}
					<div class="flex justify-start">
						<a
							href={msg.href}
							class="text-xs text-accent hover:underline"
							onclick={() => (open = false)}
						>
							Open →
						</a>
					</div>
				{/if}

				<!-- Suggestion chips -->
				{#if msg.role === 'assistant' && msg.suggestions?.length}
					<div class="flex flex-wrap gap-1.5">
						{#each msg.suggestions as suggestion}
							<button
								class="cursor-pointer rounded-full border border-border px-2.5 py-1 text-xs text-muted transition-colors hover:border-accent hover:text-accent"
								onclick={() => handleSend(suggestion)}
								disabled={sending}
							>
								{suggestion}
							</button>
						{/each}
					</div>
				{/if}
			{/each}

			{#if sending}
				<div class="flex justify-start">
					<div class="rounded-lg bg-card px-3 py-2 text-sm text-muted">
						Thinking...
					</div>
				</div>
			{/if}
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
					disabled={sending}
				/>
				<button
					class="cursor-pointer rounded-lg bg-accent px-3 py-2 text-sm text-white transition-all hover:brightness-110 disabled:opacity-50"
					onclick={() => handleSend()}
					aria-label="Send message"
					disabled={sending}
				>
					↑
				</button>
			</div>
		</div>
	</aside>
{/if}
