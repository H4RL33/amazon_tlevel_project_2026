<script lang="ts">
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { getAlbumDetail } from '$lib/api/albums';
  import { getContent } from '$lib/api/content';
  import type { AlbumDetailResponse, ContentDetailResponse } from '$lib/api/types';
  import { saveSnippet, unsaveSnippet } from '$lib/api/library';
  import { savedSnippetIds } from '$lib/stores/savedSnippets';
  import { currentUser } from '$lib/stores/user';

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

  $: snippetSaved = snippet ? $savedSnippetIds.has(snippet.id) : false;

  async function toggleSnippetSave() {
    if (!snippet) return;
    const id = snippet.id;
    if (snippetSaved) {
      savedSnippetIds.update((s) => {
        s.delete(id);
        return new Set(s);
      });
      await unsaveSnippet(id);
    } else {
      savedSnippetIds.update((s) => {
        s.add(id);
        return new Set(s);
      });
      await saveSnippet(id);
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
        <div class="snippet-header">
          <h1>{snippet.title}</h1>
          {#if $currentUser}
            <button
              class="save-btn"
              class:saved={snippetSaved}
              on:click={toggleSnippetSave}
              aria-label={snippetSaved ? 'Remove from Library' : 'Save to Library'}
              title={snippetSaved ? 'Remove from Library' : 'Save to Library'}
            >
              {#if snippetSaved}
                <svg
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                >
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              {:else}
                <svg
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
              {/if}
            </button>
          {/if}
        </div>
        <p>{snippet.body}</p>
      {/if}
    </PageCard>
  </div>
{/if}

<style>
  /* Fills the layout's scrollable .content region exactly (not more, not
     less), so the row's height never changes between Albums/Snippets and
     the page-level scroll never kicks in here — only each card's own
     overflow-y: auto does, independently.

     flex-shrink: 0: see the matching comment on .home-auth in the root
     +page.svelte — .album-page is a flex item of .content, which is itself
     a scrolling flex container, and leaving shrink at its default of 1
     breaks position: sticky for AlbumSidebar's `.sidebar-sticky` in
     Chromium. Currently a no-op in practice (same reasoning as
     .settings-page) but pinned for the same forward-safety reason. */
  .album-page {
    display: flex;
    gap: var(--gap-inner);
    height: 100%;
    flex-shrink: 0;
  }

  /* AlbumSidebar's PageCard: fixed width, never grows or shrinks. Flex's
     defaults (grow: 0, shrink: 1, basis: auto-from-width) are what let it
     shrink when the row got tight — pin all three explicitly instead. */
  .album-page > :global(.sidebar-sticky) {
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

  .snippet-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .snippet-header h1 {
    margin: 0;
    flex: 1;
  }

  .save-btn {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border: 1.5px solid #232f3e;
    border-radius: 0;
    cursor: pointer;
    color: #232f3e;
    padding: 0;
    box-shadow: 0 2px 6px rgba(35, 47, 62, 0.2);
    transition:
      background 0.15s,
      color 0.15s;
  }

  .save-btn:hover {
    background: #232f3e;
    color: #ffffff;
  }

  .save-btn.saved {
    background: #232f3e;
    color: #ffffff;
  }

  .save-btn.saved:hover {
    background: #ef4444;
    border-color: #ef4444;
  }
</style>
