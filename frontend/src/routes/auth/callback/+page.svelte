<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { exchangeCode, syncUser } from '$lib/api/auth';
  import { TOKEN_KEY } from '$lib/api/client';
  import { currentUser } from '$lib/stores/user';
  import PageCard from '$lib/components/PageCard.svelte';

  let error: string | null = null;

  onMount(async () => {
    const code = $page.url.searchParams.get('code');
    if (!code) {
      error = 'No authorization code was returned by Cognito.';
      return;
    }

    try {
      const tokens = await exchangeCode(code);
      localStorage.setItem(TOKEN_KEY, tokens.id_token);

      const claims = JSON.parse(atob(tokens.id_token.split('.')[1]));
      const user = await syncUser(claims.given_name ?? '', claims.family_name ?? '');
      currentUser.set(user);

      await goto('/');
    } catch {
      error = 'Sign-in failed. Please try again.';
    }
  });
</script>

<PageCard as="main">
  <div class="content">
    {#if error}
      <h1>Sign-in failed</h1>
      <p>{error}</p>
      <a href="/login">Back to sign in</a>
    {:else}
      <p>Signing you in...</p>
    {/if}
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
