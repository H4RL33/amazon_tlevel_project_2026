<!--
  AlbumCard
  Purpose: Square icon-tile used to open an Album — a curated, course-like set of Snippets
    forming a learning pathway. Requires an account to enrol.
  Used in: AlbumGrid (and later: CTASidebar, EnrolledAlbumsList, once those chapters land)
  Props:
    - album (AlbumListResponse): the Album to display
  Layout:
    A square tile: a large centred line-icon (looked up from album.icon) with the Album's
    title beneath it. No description or progress indicator on the card face — those live
    on the Album detail page.
  Styling:
    White background, square corners, soft directional-blur drop shadow
    (0 10px 18px -4px rgba(35, 47, 62, 0.35)), ~190px square.
-->
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;
  export let size: string | undefined = undefined;

  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: iconPaths = ICON_PATHS[album.icon] ?? DEFAULT_ICON_PATHS;
</script>

<a class="album-card" href={`/learn/${album.id}`} style={size ? `width: ${size}; height: ${size};` : undefined}>
  <svg
    class="icon"
    aria-hidden="true"
    viewBox="0 0 24 24"
    width="60"
    height="60"
    fill="none"
    stroke="#232f3e"
    stroke-width="1.3"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    {#each iconPaths as d}
      <path {d} />
    {/each}
  </svg>
  <h3>{album.title}</h3>
</a>

<style>
  .album-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    width: 190px;
    height: 190px;
    box-sizing: border-box;
    padding: 1rem;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    text-decoration: none;
    color: inherit;
  }

  .icon {
    flex-shrink: 0;
  }

  h3 {
    margin: 0;
    color: #232f3e;
    font-size: 0.95rem;
    font-weight: 700;
    text-align: center;
  }
</style>
