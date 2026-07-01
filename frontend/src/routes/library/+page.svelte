<script lang="ts">
  import type { PageData } from './$types';
  import PageCard from '$lib/components/PageCard.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';
  import AgentChat from '$lib/components/AgentChat.svelte';
  import TextInput from '$lib/components/TextInput.svelte';
  import Button from '$lib/components/Button.svelte';
  import { searchLibrary, mentorQuery, saveSnippet, unsaveSnippet } from '$lib/api/library';
  import type { ContentSearchResult, MentorResponse } from '$lib/api/library';
  import { currentUser } from '$lib/stores/user';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
  import { savedSnippetIds } from '$lib/stores/savedSnippets';

  export let data: PageData;

  let query = data.initialQuery;
  let searchResults: ContentSearchResult[] | null = null;
  let searching = false;
  let searchError = '';

  let mentorReply: MentorResponse | null = null;
  let mentorLoading = false;
  let mentorError = '';

  savedSnippetIds.set(new Set(data.library.saved_snippets.map((s) => s.id)));
  enrolledAlbumIds.set(new Set(data.library.enrolled_albums.map((a) => a.id)));

  async function handleSearch() {
    if (!query.trim()) return;
    searching = true;
    searchError = '';
    try {
      searchResults = await searchLibrary(query);
    } catch {
      searchError = 'Search failed. Please try again.';
    } finally {
      searching = false;
    }
  }

  async function handleMentor(event: CustomEvent<string>) {
    mentorLoading = true;
    mentorError = '';
    try {
      mentorReply = await mentorQuery(event.detail);
    } catch {
      mentorError = 'The mentor is unavailable right now. Please try again.';
    } finally {
      mentorLoading = false;
    }
  }

  async function toggleSave(contentId: number, currentlySaved: boolean) {
    if (currentlySaved) {
      savedSnippetIds.update((s) => {
        s.delete(contentId);
        return new Set(s);
      });
      await unsaveSnippet(contentId);
    } else {
      savedSnippetIds.update((s) => {
        s.add(contentId);
        return new Set(s);
      });
      await saveSnippet(contentId);
    }
  }
</script>

<div class="library-layout">
  <!-- Sidebar -->
  <PageCard as="aside" width="280px" padding="1.5rem" overflowY="auto">
    <div class="sidebar-inner">
      <!-- Stats -->
      <div class="stats-row">
        <PageCard padding="0.875rem 1rem">
          <div class="stat">
            <span class="stat-label">Albums</span>
            <span class="stat-value">{$enrolledAlbumIds.size}</span>
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1rem">
          <div class="stat">
            <span class="stat-label">Saved</span>
            <span class="stat-value">{$savedSnippetIds.size}</span>
          </div>
        </PageCard>
      </div>

      <!-- Search -->
      <form class="search-form" on:submit|preventDefault={handleSearch}>
        <TextInput
          bind:value={query}
          type="search"
          placeholder="Search your library…"
          disabled={searching}
        />
        <Button variant="secondary" type="submit" disabled={searching}>
          {searching ? '…' : 'Go'}
        </Button>
      </form>
      {#if searchError}
        <p class="search-error">{searchError}</p>
      {/if}

      <div class="spacer"></div>

      <!-- Dynamic Mentor -->
      <div class="mentor-section">
        <span class="section-label">Dynamic Mentor</span>
        <AgentChat placeholder="Ask your mentor anything…" on:submit={handleMentor} />
        {#if mentorLoading}
          <p class="mentor-loading">Thinking…</p>
        {/if}
        {#if mentorError}
          <p class="mentor-error">{mentorError}</p>
        {/if}
        {#if mentorReply}
          <div class="mentor-reply">
            <p>{mentorReply.reply}</p>
            {#if mentorReply.sources.length > 0}
              <div class="sources">
                <span class="sources-label">Sources:</span>
                {#each mentorReply.sources as source (source.content_id)}
                  <span class="source-chip">{source.title}</span>
                {/each}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </PageCard>

  <!-- Main -->
  <div class="library-main">
    <!-- Header -->
    <PageCard padding="1rem 1.5rem">
      <h1 class="library-heading">{$currentUser?.first_name ?? 'Your'}'s Library</h1>
    </PageCard>

    {#if searchResults !== null}
      <!-- Search results -->
      <PageCard padding="0.75rem 1.5rem">
        <div class="section-header-row">
          <span class="section-label">Search Results</span>
          <button
            class="back-btn"
            on:click={() => {
              searchResults = null;
              query = '';
            }}>← Back</button
          >
        </div>
      </PageCard>
      {#if searchResults.length === 0}
        <PageCard padding="1.5rem">
          <p class="empty">No results found for "{query}".</p>
        </PageCard>
      {:else}
        <div class="snippet-grid">
          {#each searchResults as result (result.content_id)}
            <SnippetCard
              content={{
                id: result.content_id,
                title: result.title,
                content_type: result.content_type,
              }}
              saved={$savedSnippetIds.has(result.content_id)}
              onSaveToggle={() =>
                toggleSave(result.content_id, $savedSnippetIds.has(result.content_id))}
            />
          {/each}
        </div>
      {/if}
    {:else}
      <!-- Normal library grid -->
      {#if data.library.enrolled_albums.length === 0 && $savedSnippetIds.size === 0}
        <PageCard padding="2rem">
          <p class="empty">Your library is empty. Browse Albums and Snippets to get started.</p>
        </PageCard>
      {:else}
        {#if data.library.enrolled_albums.length > 0}
          <PageCard padding="0.75rem 1.5rem">
            <span class="section-label">Enrolled Albums</span>
          </PageCard>
          <div class="album-grid">
            {#each data.library.enrolled_albums as album (album.id)}
              <AlbumCard {album} />
            {/each}
          </div>
        {/if}

        {#if $savedSnippetIds.size > 0}
          <PageCard padding="0.75rem 1.5rem">
            <span class="section-label">Saved Snippets</span>
          </PageCard>
          <div class="snippet-grid">
            {#each data.library.saved_snippets as snippet (snippet.id)}
              <SnippetCard
                content={snippet}
                saved={$savedSnippetIds.has(snippet.id)}
                onSaveToggle={() => toggleSave(snippet.id, $savedSnippetIds.has(snippet.id))}
              />
            {/each}
          </div>
        {/if}
      {/if}
    {/if}
  </div>
</div>

<style>
  .library-layout {
    display: flex;
    gap: var(--gap-inner);
    min-height: 100%;
    align-items: stretch;
  }

  /* ── Sidebar ── */
  .sidebar-inner {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
    height: 100%;
  }

  .stats-row {
    display: flex;
    gap: var(--gap-inner);
  }

  .stats-row :global(.page-card) {
    flex: 1;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .stat-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #5a6472;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  .search-form {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .search-form :global(.text-input-wrapper) {
    flex: 1;
    min-width: 0;
  }

  .search-error {
    color: #dc2626;
    font-size: 0.875rem;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .spacer {
    flex: 1;
  }

  .mentor-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .mentor-loading {
    color: #5a6472;
    font-size: 0.875rem;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .mentor-error {
    color: #dc2626;
    font-size: 0.875rem;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .mentor-reply {
    background: rgba(249, 115, 22, 0.06);
    padding: 0.875rem;
  }

  .mentor-reply p {
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
    line-height: 1.6;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
  }

  .sources-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
  }

  .source-chip {
    font-size: 0.7rem;
    background: rgba(249, 115, 22, 0.12);
    color: #c2410c;
    border-radius: 99px;
    padding: 0.15rem 0.5rem;
    font-weight: 500;
    font-family: 'Ubuntu', sans-serif;
  }

  /* ── Main ── */
  .library-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .library-heading {
    font-size: 1.25rem;
    font-weight: 800;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .section-label {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
    margin: 0;
  }

  .section-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .back-btn {
    background: none;
    border: none;
    color: #f97316;
    cursor: pointer;
    font-size: 0.875rem;
    font-family: 'Ubuntu', sans-serif;
    padding: 0;
  }

  .album-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: var(--gap-inner);
  }

  .snippet-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: var(--gap-inner);
  }

  .empty {
    color: #5a6472;
    font-size: 0.9rem;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
