<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
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

{#if loading}
  <PageCard as="main">
    <p>Loading...</p>
  </PageCard>
{:else if error || !album}
  <PageCard as="main">
    <p>{error ?? 'Album not found.'}</p>
  </PageCard>
{:else}
  <div class="album-page">
    <AlbumSidebar sides={album.sides} activeSnippetId={null} />
    <PageCard as="main">
      <h1>{album.title}</h1>
      <p>{album.description}</p>
    </PageCard>
  </div>
{/if}

<style>
  .album-page {
    display: flex;
    gap: var(--gap-inner);
  }
</style>
