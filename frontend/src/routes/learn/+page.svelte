<script lang="ts">
  import { onMount } from 'svelte';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
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

<main>
  <h1>Learn</h1>
  {#if loading}
    <p>Loading...</p>
  {:else if error}
    <p>{error}</p>
  {:else}
    <AlbumGrid {albums} />
  {/if}
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
