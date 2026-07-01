<script lang="ts">
  import { onMount } from 'svelte';
  import { getCognitoLoginUrl } from '$lib/api/auth';
  import { listAlbums } from '$lib/api/albums';
  import { apiFetch } from '$lib/api/client';
  import { getLibrary } from '$lib/api/library';
  import { getStats } from '$lib/api/users';
  import type { AlbumListResponse } from '$lib/api/types';
  import { currentUser } from '$lib/stores/user';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import CTASidebar from '$lib/components/CTASidebar.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  let albums: AlbumListResponse[] = [];
  let feedPosts: unknown[] = [];
  let loading = true;
  let albumError: string | null = null;
  let totalXp = 0;
  let snippetsCompleted = 0;
  let authedDataFetched = false;

  onMount(async () => {
    try {
      albums = await listAlbums();
    } catch {
      albumError = 'Could not load Albums right now. Please try again later.';
    } finally {
      loading = false;
    }
  });

  // Reactive rather than a one-off onMount check: currentUser is set
  // asynchronously by the root layout's getMe() call, which can resolve
  // after this page's own onMount already ran — a plain `if ($currentUser)`
  // inside onMount would silently skip these fetches in that case.
  $: if ($currentUser && !authedDataFetched) {
    authedDataFetched = true;
    Promise.allSettled([getLibrary(), getStats(), apiFetch<unknown[]>('/feed/')]).then(
      ([libResult, statsResult, feedResult]) => {
        if (libResult.status === 'fulfilled') {
          enrolledAlbumIds.set(new Set(libResult.value.enrolled_albums.map((a) => a.id)));
        }
        if (statsResult.status === 'fulfilled') {
          totalXp = statsResult.value.total_xp;
          snippetsCompleted = statsResult.value.snippets_completed;
        }
        feedPosts = feedResult.status === 'fulfilled' ? feedResult.value : [];
      }
    );
  }

  async function handleGetStarted() {
    try {
      window.location.href = await getCognitoLoginUrl();
    } catch (err) {
      console.error('Could not build Cognito login URL:', err);
    }
  }
</script>

{#if $currentUser}
  <!-- Authenticated view -->
  <div class="home-auth">
    <CTASidebar user={$currentUser} {albums} snippets={[]} />

    <div class="right-col">
      <!-- Stats row -->
      <div class="stats-row">
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">⭐ XP Earned</span>
            <span class="stat-value">{totalXp}</span>
            <span class="stat-sub">Keep learning to earn XP</span>
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">📚 Albums Enrolled</span>
            <span class="stat-value">{$enrolledAlbumIds.size}</span>
            <span class="stat-sub"
              >{$enrolledAlbumIds.size === 1 ? '1 album' : `${$enrolledAlbumIds.size} albums`}</span
            >
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">✅ Snippets Read</span>
            <span class="stat-value">{snippetsCompleted}</span>
            <span class="stat-sub"
              >{snippetsCompleted === 0
                ? 'Complete Snippets to track progress'
                : snippetsCompleted === 1
                  ? '1 snippet completed'
                  : `${snippetsCompleted} snippets completed`}</span
            >
          </div>
        </PageCard>
      </div>

      <!-- Forum header card -->
      <PageCard padding="0.875rem 1.25rem">
        <div class="forum-header">
          <div class="forum-header-left">
            <h2>The Forum</h2>
            <span class="gate-note">Hidden for under-14s · read-only for 14–16</span>
          </div>
          <NavLink href="/forum" label="View all posts →" />
        </div>
      </PageCard>

      <!-- Forum posts or empty state -->
      {#if feedPosts.length === 0}
        <PageCard padding="1.25rem">
          <p class="forum-empty">No posts yet — check back soon.</p>
        </PageCard>
      {:else}
        <div class="forum-grid">
          {#each feedPosts as _post}
            <!-- PostCard rendered here once /feed returns real Post data -->
          {/each}
        </div>
      {/if}
    </div>
  </div>
{:else}
  <!-- Guest view -->
  <div class="hero">
    <h1>Discover your future with Amazon T-Levels</h1>
    <p>
      Explore short-form content, enrol in curated learning Albums, and connect with Amazon mentors
      — all in one place.
    </p>
    <button class="cta" on:click={handleGetStarted}>Get started</button>
  </div>

  <!-- overflowY="visible": these two cards are direct children of .content
       (display: flex; flex-direction: column) in +layout.svelte, which is
       itself the page's scroll container. PageCard's default
       overflow-y: auto gives a flex item an automatic minimum size of 0
       (overflow != visible suppresses the content-based auto min-size per
       the flexbox spec), so whenever the guest homepage's total content
       height exceeds the viewport, .content's flex-shrink silently
       compresses these cards below their natural content height and
       overflow-y: auto hard-clips the difference instead of letting
       .content's own scrolling handle it — cutting a few px off the
       "Explore Albums" header and, far more visibly, chopping off the
       bottom of the AlbumGrid's last row. overflow-y: visible removes the
       auto-min-size:0 trap so these cards always render at full content
       height and let .content scroll normally. -->
  <PageCard padding="0.875rem 1.25rem" overflowY="visible">
    <div class="section-header">
      <h2>Explore Albums</h2>
      <NavLink href="/learn" label="View all →" />
    </div>
  </PageCard>

  <PageCard as="main" padding="1.5rem" overflowY="visible">
    {#if loading}
      <p class="loading">Loading...</p>
    {:else if albumError}
      <p class="error">{albumError}</p>
    {:else}
      <AlbumGrid {albums} />
    {/if}
  </PageCard>
{/if}

<style>
  /* ── Authenticated layout ── */
  /* flex-shrink: 0 is load-bearing, not defensive: .content (the scrolling
     ancestor, in +layout.svelte) is itself `display: flex; flex-direction:
     column`, so .home-auth is a flex item of a scrolling flex container.
     Left at flex's default shrink: 1, Chromium's sticky-containing-block
     computation for CTASidebar's `.sidebar-sticky` breaks entirely — its
     `position: sticky` stops sticking and it just scrolls 1:1 with
     `.content` instead (confirmed via Playwright: identical top-offset
     delta to a non-sticky element across a scroll). Pinning shrink to 0
     (min-height: 100% still lets the row grow taller than the viewport when
     .right-col's content demands it) avoids that flex-shrink/min-height
     resolution loop and restores sticky. */
  .home-auth {
    display: flex;
    gap: var(--gap-inner);
    min-height: 100%;
    align-items: stretch;
    flex-shrink: 0;
  }

  .right-col {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .stats-row {
    display: flex;
    gap: var(--gap-inner);
  }

  /* Make each PageCard stat tile share the row equally */
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

  .stat-sub {
    font-size: 0.8rem;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
  }

  .forum-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .forum-header-left {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }

  .forum-header-left h2 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .gate-note {
    font-size: 0.8rem;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
  }

  .forum-grid {
    columns: 3;
    column-gap: var(--gap-inner);
  }

  .forum-empty {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  /* ── Guest layout ── */
  .hero {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
    padding: 2.5rem 0;
  }

  .hero h1 {
    font-size: 2.25rem;
    font-weight: 800;
    color: #232f3e;
    line-height: 1.2;
    max-width: 620px;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .hero p {
    font-size: 1rem;
    color: #5a6472;
    max-width: 520px;
    line-height: 1.6;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .cta {
    background: #ffffff;
    color: #232f3e;
    border: none;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    padding: 0.7rem 1.75rem;
    font-size: 0.9rem;
    font-weight: 700;
    cursor: pointer;
    font-family: 'Ubuntu', sans-serif;
    transition: opacity 0.15s;
    margin-top: 0.25rem;
  }

  .cta:hover {
    opacity: 0.88;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .section-header h2 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .loading,
  .error {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
