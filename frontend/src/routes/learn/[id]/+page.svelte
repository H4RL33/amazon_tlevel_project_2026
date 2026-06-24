<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import { getAlbumDetail } from '$lib/api/albums';
  import type { AlbumDetailResponse } from '$lib/api/types';

  let album: AlbumDetailResponse | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    const id = Number($page.params.id);
    try {
      album = await getAlbumDetail(id);
    } catch {
      error = 'Could not load this Album right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<div class="album-page">
  {#if loading}
    <main><p>Loading...</p></main>
  {:else if error || !album}
    <main><p>{error ?? 'Album not found.'}</p></main>
  {:else}
    <AlbumSidebar sides={album.sides} activeSnippetId={null} />
    <main>
      <h1>{album.title}</h1>
      <p>{album.description}</p>
    </main>
  {/if}
</div>

<style>
  .album-page {
    display: flex;
  }

  main {
    flex-grow: 1;
    max-width: 700px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
