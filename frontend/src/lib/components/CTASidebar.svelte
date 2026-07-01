<!--
  CTASidebar
  Purpose: Wide left sidebar on the home page for authenticated users. Personalised greeting,
    up to 2 enrolled AlbumCards, up to 3 recommended SnippetCards, and an AgentChat teaser
    pinned to the bottom. Navigates to /library on AgentChat submit, carrying the typed message
    via the agentDraft store.
  Used in: / (authenticated branch)
  Props:
    - user (UserResponse): current user — greeting uses first_name, falling back to
      username then "there" when first_name isn't set (e.g. Cognito never collected it)
    - albums (AlbumListResponse[]): ALL albums (not filtered by enrollment) — this
      component filters down to the ones in enrolledAlbumIds itself, then shows up to 2.
      If the user is enrolled in 1+ but fewer than 2, the remaining slot(s) render as
      empty placeholder tiles (not just fewer cards) so the row still reads as "2 slots".
      If the user has zero enrolled albums, the "Browse Albums to get started" prompt is
      shown instead of two empty slots.
    - snippets (ContentListResponse[]): recommended snippets; first 3 shown. Section omitted if empty.
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import type { AlbumListResponse, ContentListResponse, UserResponse } from '$lib/api/types';
  import { saveSnippet, unsaveSnippet } from '$lib/api/library';
  import { savedSnippetIds } from '$lib/stores/savedSnippets';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
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
  $: displayName = user.first_name || user.username || 'there';
  $: enrolledAlbums = albums.filter((a) => $enrolledAlbumIds.has(a.id));
  $: displayedAlbums = enrolledAlbums.slice(0, 2);
  // Only pad with empty slots when the user has *some* enrolled albums but fewer than the
  // 2-slot layout wants — zero enrolled albums keeps the "Browse Albums" empty state instead.
  $: emptySlotCount = displayedAlbums.length > 0 ? 2 - displayedAlbums.length : 0;
  $: displayedSnippets = snippets.slice(0, 3);

  async function toggleSnippetSave(contentId: number, currentlySaved: boolean) {
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

  function handleAgentSubmit(event: CustomEvent<string>) {
    goto(`/library?q=${encodeURIComponent(event.detail)}`);
  }
</script>

<PageCard as="aside" width="360px" padding="1.5rem" overflowY="visible">
  <div class="sidebar-inner">
    <p class="greeting">Good {timeOfDay}, {displayName} 👋</p>

    <div class="section">
      <span class="section-label">Your Albums</span>
      {#if displayedAlbums.length > 0}
        <div class="album-row">
          {#each displayedAlbums as album}
            <div class="album-slot">
              <AlbumCard {album} size="100%" />
            </div>
          {/each}
          {#each Array(emptySlotCount) as _}
            <div class="album-slot album-slot-empty" aria-hidden="true"></div>
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
            <SnippetCard
              content={snippet}
              saved={$savedSnippetIds.has(snippet.id)}
              onSaveToggle={() => toggleSnippetSave(snippet.id, $savedSnippetIds.has(snippet.id))}
            />
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
  }

  /* Placeholder tile shown when the user has fewer enrolled albums than slots available */
  .album-slot-empty {
    border: 1.5px dashed #c7ccd3;
    background: rgba(90, 100, 114, 0.04);
    box-sizing: border-box;
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
