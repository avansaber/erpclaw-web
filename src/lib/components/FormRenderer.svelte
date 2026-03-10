<script lang="ts">
	import type { FormSpec } from '$lib/types';
	import { fly } from 'svelte/transition';

	let {
		spec,
		onSubmit,
		loading = false
	}: {
		spec: FormSpec;
		onSubmit: (data: Record<string, unknown>) => void | Promise<void>;
		loading?: boolean;
	} = $props();

	let formData = $state<Record<string, unknown>>({});
	let submitted = $state(false);
	let submitting = $state(false);
	let touched = $state<Record<string, boolean>>({});

	async function handleSubmit() {
		submitting = true;
		try {
			await onSubmit(formData);
			submitted = true;
			setTimeout(() => (submitted = false), 2000);
		} finally {
			submitting = false;
		}
	}

	function handleBlur(fieldName: string) {
		touched[fieldName] = true;
	}

	function isFieldMissing(fieldName: string, required?: boolean): boolean {
		if (!required || !touched[fieldName]) return false;
		const val = formData[fieldName];
		return val == null || val === '';
	}

	function fieldId(fieldName: string): string {
		return `field-${fieldName}`;
	}

	let isSubmitting = $derived(submitting || loading);
</script>

<form
	class="max-w-2xl"
	in:fly={{ y: 8, duration: 200 }}
	onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}
>
	{#each spec.sections as section, si}
		<fieldset
			class="mb-4 rounded-xl border border-border bg-card p-5"
			in:fly={{ y: 8, delay: si * 80, duration: 250 }}
			disabled={isSubmitting}
		>
			<legend class="mb-3 text-xs font-medium uppercase tracking-wider text-muted">{section.label}</legend>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				{#each section.fields as field}
					<div class:sm:col-span-2={field.type === 'textarea'}>
						<label for={fieldId(field.name)} class="mb-1 block text-xs text-muted">
							{field.label}
							{#if field.required}<span class="text-red" aria-hidden="true"> *</span>{/if}
						</label>
						{#if field.type === 'select'}
							<select
								id={fieldId(field.name)}
								bind:value={formData[field.name]}
								onblur={() => handleBlur(field.name)}
								required={field.required}
								aria-required={field.required}
								aria-invalid={isFieldMissing(field.name, field.required)}
								class="w-full rounded-md border bg-surface p-2 text-sm text-text outline-none transition-colors focus:border-accent
								{isFieldMissing(field.name, field.required) ? 'border-red' : 'border-border'}"
							>
								<option value="">Select...</option>
								{#each field.options ?? [] as opt}
									<option value={opt}>{opt}</option>
								{/each}
							</select>
						{:else if field.type === 'textarea'}
							<textarea
								id={fieldId(field.name)}
								bind:value={formData[field.name]}
								onblur={() => handleBlur(field.name)}
								placeholder={field.placeholder}
								required={field.required}
								aria-required={field.required}
								aria-invalid={isFieldMissing(field.name, field.required)}
								class="w-full rounded-md border bg-surface p-2 text-sm text-text outline-none transition-colors focus:border-accent
								{isFieldMissing(field.name, field.required) ? 'border-red' : 'border-border'}"
								rows="2"
							></textarea>
						{:else}
							<input
								id={fieldId(field.name)}
								type={field.type === 'currency' ? 'text' : field.type}
								bind:value={formData[field.name]}
								onblur={() => handleBlur(field.name)}
								placeholder={field.placeholder ?? ''}
								required={field.required}
								aria-required={field.required}
								aria-invalid={isFieldMissing(field.name, field.required)}
								class="w-full rounded-md border bg-surface p-2 text-sm text-text outline-none transition-colors focus:border-accent
								{isFieldMissing(field.name, field.required) ? 'border-red' : 'border-border'}"
							/>
						{/if}
						{#if isFieldMissing(field.name, field.required)}
							<p class="mt-1 text-xs text-red" role="alert">{field.label} is required</p>
						{/if}
					</div>
				{/each}
			</div>
		</fieldset>
	{/each}

	<button
		type="submit"
		disabled={isSubmitting}
		class="cursor-pointer rounded-lg px-5 py-2.5 text-sm font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
		style:background="var(--color-accent)"
	>
		{#if submitted}
			&#10003; Saved
		{:else if isSubmitting}
			Saving...
		{:else}
			{spec.submitLabel}
		{/if}
	</button>
</form>
