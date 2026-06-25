<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
  import { getCognitoLoginUrl } from '$lib/api/auth';

  let error: string | null = null;

  async function handleLoginClick() {
    error = null;
    try {
      window.location.href = await getCognitoLoginUrl();
    } catch (err) {
      console.error('Could not build Cognito login URL:', err);
      error = 'Could not start sign-in. Please try again.';
    }
  }
</script>

<PageCard as="main">
  <div class="content">
    <h1>Sign in</h1>
    <p>
      Sign in to enrol in Albums, track your progress, and use The Library. You can keep browsing
      Snippets and Topics without an account.
    </p>
    <button type="button" on:click={handleLoginClick}>Log in with Cognito</button>
    {#if error}
      <p role="alert">{error}</p>
    {/if}
    <a href="/">Back to Home</a>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }

  a {
    color: #1f6feb;
  }

  button {
    display: block;
    margin: 1rem 0;
    padding: 0.625rem 1.25rem;
    font-size: 0.9375rem;
    font-weight: 500;
    color: #fff;
    background: #232f3e;
    border: none;
    border-radius: 6px;
    cursor: pointer;
  }

  button:hover,
  button:focus-visible {
    background: #364252;
  }
</style>
