<script lang="ts">
  import type { PageData } from './$types';
  import PageCard from '$lib/components/PageCard.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';
  import AgentChat from '$lib/components/AgentChat.svelte';
  import { searchLibrary, mentorQuery, saveSnippet, unsaveSnippet } from '$lib/api/library';
  import type { ContentSearchResult, MentorResponse } from '$lib/api/library';

  export let data: PageData;

  let query = data.initialQuery;
  let searchResults: ContentSearchResult[] | null = null;
  let searching = false;
  let searchError = '';

  let mentorReply: MentorResponse | null = null;
  let mentorLoading = false;
  let mentorError = '';

  let savedIds = new Set(data.library.saved_snippets.map((s) => s.id));

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
      savedIds.delete(contentId);
      savedIds = new Set(savedIds);
      await unsaveSnippet(contentId);
    } else {
      savedIds.add(contentId);
      savedIds = new Set(savedIds);
      await saveSnippet(contentId);
    }
  }
</script>

<div class="library-layout">
  <PageCard padding="1rem 1.5rem">
    <form class="search-bar" on:submit|preventDefault={handleSearch}>
      <input
        bind:value={query}
        type="search"
        placeholder="Search your learning materials..."
        class="search-input"
      />
      <button type="submit" class="search-btn" disabled={searching}>
        {searching ? 'Searching…' : 'Search'}
      </button>
    </form>
    {#if searchError}
      <p class="error">{searchError}</p>
    {/if}
  </PageCard>

  {#if searchResults !== null}
    <PageCard padding="1.5rem">
      <h2 class="section-heading">Search Results</h2>
      {#if searchResults.length === 0}
        <p class="empty">No results found for "{query}".</p>
      {:else}
        <div class="snippet-grid">
          {#each searchResults as result (result.content_id)}
            <SnippetCard
              content={{
                id: result.content_id,
                title: result.title,
                content_type: result.content_type,
              }}
              saved={savedIds.has(result.content_id)}
              onSaveToggle={() => toggleSave(result.content_id, savedIds.has(result.content_id))}
            />
          {/each}
        </div>
      {/if}
      <button
        class="clear-btn"
        on:click={() => {
          searchResults = null;
          query = '';
        }}
      >
        ← Back to library
      </button>
    </PageCard>
  {:else}
    <div class="library-columns">
      <div class="column">
        <PageCard padding="1.5rem" overflowY="hidden">
          <h2 class="section-heading">Enrolled Albums</h2>
        </PageCard>
        {#if data.library.enrolled_albums.length === 0}
          <PageCard padding="1.5rem">
            <p class="empty">You haven't enrolled in any albums yet.</p>
          </PageCard>
        {:else}
          {#each data.library.enrolled_albums as album (album.id)}
            <AlbumCard {album} />
          {/each}
        {/if}
      </div>

      <div class="column">
        <PageCard padding="1.5rem" overflowY="hidden">
          <h2 class="section-heading">Saved Snippets</h2>
        </PageCard>
        {#if data.library.saved_snippets.length === 0}
          <PageCard padding="1.5rem">
            <p class="empty">You haven't saved any snippets yet.</p>
          </PageCard>
        {:else}
          <div class="snippet-grid padded">
            {#each data.library.saved_snippets as snippet (snippet.id)}
              <SnippetCard
                content={snippet}
                saved={savedIds.has(snippet.id)}
                onSaveToggle={() => toggleSave(snippet.id, savedIds.has(snippet.id))}
              />
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <PageCard padding="1.5rem">
    <h2 class="section-heading">Dynamic Mentor</h2>
    <AgentChat
      placeholder="Ask your mentor anything about your saved content..."
      on:submit={handleMentor}
    />
    {#if mentorLoading}
      <p class="mentor-loading">Thinking…</p>
    {/if}
    {#if mentorError}
      <p class="error">{mentorError}</p>
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
  </PageCard>
</div>

<style>
  .library-layout {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner, 0.75rem);
    max-width: 1100px;
    margin: 0 auto;
    width: 100%;
  }

  .search-bar {
    display: flex;
    gap: 0.75rem;
  }

  .search-input {
    flex: 1;
    padding: 0.65rem 1rem;
    border: 1px solid rgba(35, 47, 62, 0.2);
    border-radius: 8px;
    font-size: 0.95rem;
    outline: none;
  }

  .search-input:focus {
    border-color: #f97316;
  }

  .search-btn {
    padding: 0.65rem 1.25rem;
    background: linear-gradient(to right, #f97316, #facc15);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    color: white;
  }

  .search-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .library-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--gap-inner, 0.75rem);
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner, 0.75rem);
  }

  .snippet-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .snippet-grid.padded {
    padding: 0.5rem;
  }

  .section-heading {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #232f3e;
  }

  .empty {
    color: #5a6472;
    font-size: 0.9rem;
    margin: 0;
  }

  .error {
    color: #dc2626;
    font-size: 0.875rem;
    margin: 0.5rem 0 0;
  }

  .clear-btn {
    margin-top: 1rem;
    background: none;
    border: none;
    color: #f97316;
    cursor: pointer;
    font-size: 0.9rem;
    padding: 0;
  }

  .mentor-loading {
    color: #5a6472;
    font-size: 0.9rem;
    margin: 0.75rem 0 0;
  }

  .mentor-reply {
    margin-top: 1rem;
    background: rgba(249, 115, 22, 0.06);
    border-radius: 8px;
    padding: 1rem;
  }

  .mentor-reply p {
    margin: 0 0 0.75rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #232f3e;
  }

  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }

  .sources-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #5a6472;
  }

  .source-chip {
    font-size: 0.75rem;
    background: rgba(249, 115, 22, 0.12);
    color: #c2410c;
    border-radius: 99px;
    padding: 0.2rem 0.6rem;
    font-weight: 500;
  }
</style>
