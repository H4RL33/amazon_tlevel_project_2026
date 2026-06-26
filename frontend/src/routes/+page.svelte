<script lang="ts">
  import { onMount } from 'svelte';
  import { getCognitoLoginUrl } from '$lib/api/auth';
  import { listAlbums } from '$lib/api/albums';
  import { apiFetch } from '$lib/api/client';
  import type { AlbumListResponse } from '$lib/api/types';
  import { currentUser } from '$lib/stores/user';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import CTASidebar from '$lib/components/CTASidebar.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  let albums: AlbumListResponse[] = [];
  let feedPosts: unknown[] = [];
  let loading = true;
  let albumError: string | null = null;

  onMount(async () => {
    try {
      albums = await listAlbums();
    } catch {
      albumError = 'Could not load Albums right now. Please try again later.';
    } finally {
      loading = false;
    }

    if ($currentUser) {
      try {
        feedPosts = await apiFetch<unknown[]>('/feed/');
      } catch {
        feedPosts = [];
      }
    }
  });

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
            <span class="stat-value">0</span>
            <span class="stat-sub">Keep learning to earn XP</span>
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">📚 Albums Enrolled</span>
            <span class="stat-value">{albums.length}</span>
            <span class="stat-sub"
              >{albums.length === 1 ? '1 album' : `${albums.length} albums`}</span
            >
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">✅ Snippets Read</span>
            <span class="stat-value">0</span>
            <span class="stat-sub">Complete Snippets to track progress</span>
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

  <PageCard padding="0.875rem 1.25rem">
    <div class="section-header">
      <h2>Explore Albums</h2>
      <NavLink href="/learn" label="View all →" />
    </div>
  </PageCard>

  <PageCard as="main" padding="1.5rem">
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
  .home-auth {
    display: flex;
    gap: var(--gap-inner);
    min-height: 100%;
    align-items: stretch;
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
    font-size: 0.7rem;
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
    font-size: 0.72rem;
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
    font-size: 0.75rem;
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
