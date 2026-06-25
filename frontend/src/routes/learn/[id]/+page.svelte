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
  /* Fills the layout's scrollable .content region exactly (not more, not
     less), so the row's height never changes between Albums/Snippets and
     the page-level scroll never kicks in here — only each card's own
     overflow-y: auto does, independently. */
  .album-page {
    display: flex;
    gap: var(--gap-inner);
    height: 100%;
  }

  /* AlbumSidebar's PageCard: fixed width, never grows or shrinks. Flex's
     defaults (grow: 0, shrink: 1, basis: auto-from-width) are what let it
     shrink when the row got tight — pin all three explicitly instead. */
  .album-page > :global(aside.page-card) {
    flex: 0 0 288px;
  }

  /* Main content card: fills exactly the remaining row width. min-width: 0
     overrides flex's default min-width: auto, which otherwise refuses to
     shrink below the content's intrinsic width and was why long Snippet
     bodies could grow this card (and the row) wider than intended. */
  .album-page > :global(main.page-card) {
    flex: 1 1 auto;
    min-width: 0;
  }
</style>
