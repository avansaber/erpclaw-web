<script lang="ts">
	import { auth } from '$lib/auth';
	import { goto } from '$app/navigation';

	let username = $state('');
	let email = $state('');
	let fullName = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		loading = true;
		const result = await auth.setup(username, email, fullName, password);

		if (result.error) {
			error = result.error;
			loading = false;
			return;
		}

		// Auto-login after setup
		const loginResult = await auth.login(email, password);
		if (loginResult.ok) {
			goto('/');
		} else {
			// Setup succeeded but login failed — go to login page
			goto('/login');
		}
		loading = false;
	}
</script>

<div class="flex min-h-screen items-center justify-center p-4">
	<div class="w-full max-w-md space-y-8">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-accent">ERPClaw Setup</h1>
			<p class="mt-1 text-sm text-muted">Create your administrator account</p>
		</div>

		<form onsubmit={handleSubmit} class="space-y-4 rounded-xl border border-border bg-card p-6">
			{#if error}
				<div class="rounded-lg bg-red/10 px-3 py-2 text-sm text-red" role="alert">
					{error}
				</div>
			{/if}

			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="username" class="block text-xs font-medium text-muted">Username</label>
					<input
						id="username"
						type="text"
						bind:value={username}
						required
						autocomplete="username"
						class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
						placeholder="admin"
					/>
				</div>
				<div>
					<label for="fullName" class="block text-xs font-medium text-muted">Full Name</label>
					<input
						id="fullName"
						type="text"
						bind:value={fullName}
						required
						class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
						placeholder="Nikhil Kumar"
					/>
				</div>
			</div>

			<div>
				<label for="email" class="block text-xs font-medium text-muted">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					autocomplete="email"
					class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
					placeholder="admin@erpclaw.ai"
				/>
			</div>

			<div>
				<label for="password" class="block text-xs font-medium text-muted">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					autocomplete="new-password"
					class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
					placeholder="Min 8 chars, 1 upper, 1 lower, 1 digit"
				/>
			</div>

			<div>
				<label for="confirmPassword" class="block text-xs font-medium text-muted">Confirm Password</label>
				<input
					id="confirmPassword"
					type="password"
					bind:value={confirmPassword}
					required
					autocomplete="new-password"
					class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
					placeholder="••••••••"
				/>
			</div>

			<button
				type="submit"
				disabled={loading}
				class="w-full cursor-pointer rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{loading ? 'Creating account...' : 'Create Admin Account'}
			</button>
		</form>
	</div>
</div>
