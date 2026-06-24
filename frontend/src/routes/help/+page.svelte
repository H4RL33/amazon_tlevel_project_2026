<script lang="ts">
  import HelpPanel from '$lib/components/HelpPanel.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Help</h1>
    <HelpPanel />
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
