<script lang="ts">
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { getAlbumDetail } from '$lib/api/albums';
  import { getContent } from '$lib/api/content';
  import type { AlbumDetailResponse, ContentDetailResponse } from '$lib/api/types';

  let album: AlbumDetailResponse | null = null;
  let loading = true;
  let error: string | null = null;

  let snippet: ContentDetailResponse | null = null;
  let snippetLoading = false;
  let snippetError: string | null = null;

  $: albumId = Number($page.params.id);
  $: snippetIdParam = $page.url.searchParams.get('snippet');
  $: activeSnippetId = snippetIdParam ? Number(snippetIdParam) : null;

  $: loadAlbum(albumId);
  $: loadSnippet(activeSnippetId);

  async function loadAlbum(id: number) {
    loading = true;
    try {
      album = await getAlbumDetail(id);
    } catch {
      error = 'Could not load this Album right now. Please try again later.';
    } finally {
      loading = false;
    }
  }

  async function loadSnippet(id: number | null) {
    if (id === null) {
      snippet = null;
      snippetError = null;
      return;
    }
    snippetLoading = true;
    snippetError = null;
    try {
      snippet = await getContent(id);
    } catch {
      snippetError = 'Could not load this Snippet right now. Please try again later.';
    } finally {
      snippetLoading = false;
    }
  }
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
    <AlbumSidebar sides={album.sides} {activeSnippetId} />
    <PageCard as="main">
      {#if activeSnippetId === null}
        <h1>{album.title}</h1>
        <p>{album.description}</p>
      {:else if snippetLoading}
        <p>Loading...</p>
      {:else if snippetError || !snippet}
        <p>{snippetError ?? 'Snippet not found.'}</p>
      {:else}
        <h1>{snippet.title}</h1>
        <p>{snippet.body}</p>
      {/if}
    </PageCard>
  </div>
{/if}

<style>
  .album-page {
    display: flex;
    gap: var(--gap-inner);
  }
</style>
