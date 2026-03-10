<script lang="ts">
	import '../app.css';
	import SidebarNav from '$lib/components/SidebarNav.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import ChatPanel from '$lib/components/ChatPanel.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import { layout, loadVerticals } from '$lib/stores';
	import { auth, user, isAuthenticated, isLoading } from '$lib/auth';
	import { connectWS, disconnectWS } from '$lib/websocket';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount, onDestroy } from 'svelte';

	let { children } = $props();

	let cmdOpen = $state(false);
	let chatOpen = $state(false);
	let sidebarOpen = $state(false);
	let userMenuOpen = $state(false);
	let apiAvailable = $state(false);

	let activeEntity = $derived(() => {
		const path = $page.url.pathname;
		if (path === '/' || path === '/login' || path === '/setup') return '';
		return path.split('/')[1] ?? '';
	});

	// Human-readable label for breadcrumb
	let activeEntityLabel = $derived(() => {
		const key = activeEntity();
		if (!key) return '';
		const def = $layout.entities[key];
		return def?.labelPlural ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
	});

	// Public routes that don't need auth
	let isPublicRoute = $derived(
		$page.url.pathname === '/login' || $page.url.pathname === '/setup'
	);

	onMount(async () => {
		// Check if API is available
		const setupRequired = await auth.checkSetup();

		let authState: { setupRequired: boolean | null } = { setupRequired: null };
		auth.subscribe((s) => {
			authState = s;
			apiAvailable = s.setupRequired !== null;
		})();

		if (apiAvailable) {
			if (setupRequired) {
				goto('/setup');
				return;
			}

			// Try to restore session
			const restored = await auth.refresh();
			if (!restored && $page.url.pathname !== '/login') {
				goto('/login');
				return;
			}

			// Load verticals from API
			await loadVerticals();

			// Connect WebSocket for real-time updates
			connectWS();
		}
		// If API not available, mock mode — no auth needed
	});

	onDestroy(() => {
		disconnectWS();
	});

	function handleGlobalKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
			e.preventDefault();
			cmdOpen = !cmdOpen;
		}
		if (e.key === 'Escape' && sidebarOpen) {
			sidebarOpen = false;
		}
		if (e.key === 'Escape' && userMenuOpen) {
			userMenuOpen = false;
		}
	}

	async function handleLogout() {
		userMenuOpen = false;
		disconnectWS();
		await auth.logout();
		goto('/login');
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<!-- Public pages (login, setup) render without chrome -->
{#if isPublicRoute}
	{@render children()}
{:else}
	<!-- Skip nav link -->
	<a
		href="#main-content"
		class="fixed left-0 top-0 z-[100] -translate-y-full rounded-br-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-transform focus:translate-y-0"
	>
		Skip to content
	</a>

	<div class="flex h-screen overflow-hidden">
		<!-- Mobile sidebar backdrop -->
		{#if sidebarOpen}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="fixed inset-0 z-30 bg-black/50 md:hidden"
				onclick={() => (sidebarOpen = false)}
				onkeydown={(e) => e.key === 'Escape' && (sidebarOpen = false)}
			></div>
		{/if}

		<!-- Sidebar -->
		<div
			class="fixed inset-y-0 left-0 z-40 w-56 transform transition-transform duration-200 md:static md:translate-x-0
			{sidebarOpen ? 'translate-x-0' : '-translate-x-full'}"
		>
			<SidebarNav groups={$layout.sidebar} activeEntity={activeEntity()} />
		</div>

		<div class="flex flex-1 flex-col overflow-hidden">
			<!-- Header -->
			<header class="flex items-center justify-between border-b border-border bg-surface px-4 py-3 md:px-6">
				<div class="flex items-center gap-3">
					<button
						class="cursor-pointer rounded-md p-1 text-muted hover:text-text md:hidden"
						onclick={() => (sidebarOpen = !sidebarOpen)}
						aria-label="Toggle sidebar"
					>
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>

					<a href="/" class="text-sm font-bold text-accent">ERPClaw</a>
					{#if activeEntity()}
						<span class="text-muted">/</span>
						<span class="text-sm">{activeEntityLabel()}</span>
					{/if}
				</div>
				<div class="flex items-center gap-2">
					<button
						class="hidden cursor-pointer rounded-lg border border-border px-3 py-1.5 text-xs text-muted transition-colors hover:border-accent hover:text-accent sm:block"
						onclick={() => (cmdOpen = true)}
					>
						&#8984;K Search
					</button>
					<button
						class="cursor-pointer rounded-lg border border-border px-3 py-1.5 text-xs text-muted transition-colors hover:border-accent hover:text-accent sm:hidden"
						onclick={() => (cmdOpen = true)}
						aria-label="Search"
					>
						&#x1F50D;
					</button>
					<button
						class="cursor-pointer rounded-md border border-border p-1.5 text-xs text-muted transition-colors hover:border-accent hover:text-accent"
						onclick={() => (chatOpen = !chatOpen)}
						aria-label="Toggle assistant chat"
					>
						&#x1F4AC;
					</button>

					<!-- User avatar / menu -->
					<div class="relative">
						<button
							class="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-accent/20 text-xs text-accent"
							onclick={() => (userMenuOpen = !userMenuOpen)}
							aria-label="User menu"
						>
							{$user ? $user.username.slice(0, 2).toUpperCase() : 'NK'}
						</button>

						{#if userMenuOpen}
							<div class="absolute right-0 top-10 z-50 w-48 rounded-lg border border-border bg-card py-1 shadow-lg">
								{#if $user}
									<div class="border-b border-border px-3 py-2">
										<p class="text-sm font-medium">{$user.full_name}</p>
										<p class="text-xs text-muted">{$user.email}</p>
									</div>
									<button
										class="w-full cursor-pointer px-3 py-2 text-left text-sm text-muted transition-colors hover:bg-surface hover:text-text"
										onclick={handleLogout}
									>
										Sign Out
									</button>
								{:else}
									<a
										href="/login"
										class="block px-3 py-2 text-sm text-muted transition-colors hover:bg-surface hover:text-text"
										onclick={() => (userMenuOpen = false)}
									>
										Sign In
									</a>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</header>

			<!-- Content + Chat -->
			<div class="flex flex-1 overflow-hidden">
				<main id="main-content" class="flex-1 overflow-y-auto p-4 md:p-6" tabindex="-1">
					{@render children()}
				</main>

				<ChatPanel bind:open={chatOpen} />
			</div>
		</div>
	</div>

	<CommandPalette bind:open={cmdOpen} />
{/if}

<ToastContainer />
