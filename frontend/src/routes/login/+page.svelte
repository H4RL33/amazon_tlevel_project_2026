<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Sign in</h1>
    <p>
      Sign-in is coming soon. In the meantime, you can keep browsing Snippets, Albums, and Topics
      without an account.
    </p>
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
</style>
