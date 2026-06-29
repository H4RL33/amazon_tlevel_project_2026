<!--
  CTASidebar
  Purpose: Wide left sidebar on the home page for authenticated users. Personalised greeting,
    up to 2 enrolled AlbumCards, up to 3 recommended SnippetCards, and an AgentChat teaser
    pinned to the bottom. Navigates to /library on AgentChat submit, carrying the typed message
    via the agentDraft store.
  Used in: / (authenticated branch)
  Props:
    - user (UserResponse): current user — provides first_name for the greeting
    - albums (AlbumListResponse[]): all albums; first 2 shown. Empty state shown if empty.
    - snippets (ContentListResponse[]): recommended snippets; first 3 shown. Section omitted if empty.
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import type { AlbumListResponse, ContentListResponse, UserResponse } from '$lib/api/types';
  import AgentChat from '$lib/components/AgentChat.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';

  export let user: UserResponse;
  export let albums: AlbumListResponse[];
  export let snippets: ContentListResponse[];

  $: hour = new Date().getHours();
  $: timeOfDay = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
  $: displayedAlbums = albums.slice(0, 2);
  $: displayedSnippets = snippets.slice(0, 3);

  function handleAgentSubmit(event: CustomEvent<string>) {
    goto(`/library?q=${encodeURIComponent(event.detail)}`);
  }
</script>

<PageCard as="aside" width="280px" padding="1.5rem" overflowY="visible">
  <div class="sidebar-inner">
    <p class="greeting">Good {timeOfDay}, {user.first_name} 👋</p>

    <div class="section">
      <span class="section-label">Your Albums</span>
      {#if displayedAlbums.length > 0}
        <div class="album-row">
          {#each displayedAlbums as album}
            <div class="album-slot">
              <AlbumCard {album} size="100%" />
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-text">Browse Albums to get started</p>
        <NavLink href="/learn" label="Browse Albums" />
      {/if}
    </div>

    {#if displayedSnippets.length > 0}
      <div class="section">
        <span class="section-label">Recommended Snippets</span>
        <div class="snippet-list">
          {#each displayedSnippets as snippet}
            <SnippetCard content={snippet} />
          {/each}
        </div>
      </div>
    {/if}

    <div class="spacer"></div>

    <AgentChat on:submit={handleAgentSubmit} />
  </div>
</PageCard>

<style>
  .sidebar-inner {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
    height: 100%;
  }

  .greeting {
    font-size: 1rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-label {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5a6472;
  }

  /* Two AlbumCards side by side, each a square filling its flex slot */
  .album-row {
    display: flex;
    flex-direction: row;
    gap: var(--gap-inner);
  }

  .album-slot {
    flex: 1;
    min-width: 0;
    aspect-ratio: 1;
    max-height: 90px;
  }

  .snippet-list {
    display: flex;
    flex-direction: column;
    gap: calc(var(--gap-inner) * 0.5);
  }

  .empty-text {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  /* Pushes AgentChat to the bottom of the sidebar */
  .spacer {
    flex: 1;
  }
</style>
