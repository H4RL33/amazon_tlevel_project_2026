<script lang="ts">
  import { onMount } from 'svelte';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { listAlbums } from '$lib/api/albums';
  import type { AlbumListResponse } from '$lib/api/types';

  let albums: AlbumListResponse[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      albums = await listAlbums();
    } catch {
      error = 'Could not load Albums right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<PageCard as="main">
  <div class="content">
    <h1>Learn</h1>
    {#if loading}
      <p>Loading...</p>
    {:else if error}
      <p>{error}</p>
    {:else}
      <AlbumGrid {albums} />
    {/if}
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
