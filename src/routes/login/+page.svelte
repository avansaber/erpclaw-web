<script lang="ts">
	import { auth } from '$lib/auth';
	import { goto } from '$app/navigation';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		const result = await auth.login(email, password);

		if (result.ok) {
			goto('/');
		} else {
			error = result.error ?? 'Login failed';
		}
		loading = false;
	}
</script>

<div class="flex min-h-screen items-center justify-center p-4">
	<div class="w-full max-w-sm space-y-8">
		<!-- Logo -->
		<div class="text-center">
			<h1 class="text-2xl font-bold text-accent">ERPClaw</h1>
			<p class="mt-1 text-sm text-muted">Sign in to your account</p>
		</div>

		<!-- Login form -->
		<form onsubmit={handleSubmit} class="space-y-4 rounded-xl border border-border bg-card p-6">
			{#if error}
				<div class="rounded-lg bg-red/10 px-3 py-2 text-sm text-red" role="alert">
					{error}
				</div>
			{/if}

			<div>
				<label for="email" class="block text-xs font-medium text-muted">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					autocomplete="email"
					class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
					placeholder="admin@example.com"
				/>
			</div>

			<div>
				<label for="password" class="block text-xs font-medium text-muted">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					autocomplete="current-password"
					class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
					placeholder="••••••••"
				/>
			</div>

			<button
				type="submit"
				disabled={loading}
				class="w-full cursor-pointer rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{loading ? 'Signing in...' : 'Sign In'}
			</button>
		</form>

		<p class="text-center text-xs text-muted">
			No account? Ask your administrator.
		</p>
	</div>
</div>
