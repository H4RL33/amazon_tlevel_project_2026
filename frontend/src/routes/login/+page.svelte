<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
  import Button from '$lib/components/Button.svelte';
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
    <div class="btn-row">
      <Button variant="primary" type="button" on:click={handleLoginClick}>
        Log in with Cognito
      </Button>
    </div>
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

  .btn-row {
    margin: 1rem 0;
  }

  a {
    color: #1f6feb;
  }
</style>
