<!--
  AlbumCard
  Purpose: Wide card used to open an Album — a curated, course-like set of Snippets forming a
    learning pathway. Requires an account to enrol.
  Used in: AlbumGrid (and later: CTASidebar, EnrolledAlbumsList, once those chapters land)
  Props:
    - album (AlbumListResponse): the Album to display
    - progress (number | null): Snippets read out of the Album's total. null if not enrolled
      or not logged in -- always null until auth/enrolment exist.
  Layout:
    Left: square icon portion (decorative emoji, looked up from album.icon).
    Right: album.title, album.description as subtitle, and a ProgressBar only when progress
      is not null.
  Styling:
    Card base, flex row, left square ~80px, right column flex-grow.
-->
<script lang="ts">
  import ProgressBar from '$lib/components/ProgressBar.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;
  export let progress: number | null = null;

  const ICONS: Record<string, string> = {
    cloud: '☁️',
  };
  const DEFAULT_ICON = '📦';

  $: icon = ICONS[album.icon] ?? DEFAULT_ICON;
</script>

<a class="album-card" href={`/learn/${album.id}`}>
  <div class="icon" aria-hidden="true">{icon}</div>
  <div class="info">
    <h3>{album.title}</h3>
    <p>{album.description}</p>
    {#if progress !== null}
      <ProgressBar pct={progress} />
    {/if}
  </div>
</a>

<style>
  .album-card {
    display: flex;
    gap: 1rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1rem;
    text-decoration: none;
    color: inherit;
  }

  .icon {
    flex-shrink: 0;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    background: #0d1117;
    border-radius: 6px;
  }

  .info {
    flex-grow: 1;
    min-width: 0;
  }

  .info h3 {
    margin: 0 0 0.25rem;
    color: #c9d1d9;
    font-size: 1rem;
  }

  .info p {
    margin: 0;
    color: #8b949e;
    font-size: 0.875rem;
    line-height: 1.5;
  }
</style>
