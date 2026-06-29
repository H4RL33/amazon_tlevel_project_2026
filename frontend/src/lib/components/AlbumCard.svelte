<!--
  AlbumCard
  Purpose: Square icon-tile for Albums or Topics. In album mode (album prop set), links to
    /learn/[id] and shows album title. In topic mode (href + label set, no album), links to
    the provided href with the provided label. Used in AlbumGrid, CTASidebar, and the
    /t-levels index page.
  Props:
    - album (AlbumListResponse | undefined): the Album to display. Optional.
    - href (string | undefined): overrides the link destination when set.
    - label (string | undefined): overrides the displayed title when set.
    - size (string | undefined): CSS size override (width and height), e.g. "100%".
-->
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse | undefined = undefined;
  export let href: string | undefined = undefined;
  export let label: string | undefined = undefined;
  export let size: string | undefined = undefined;

  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: resolvedHref = href ?? (album ? `/learn/${album.id}` : '/');
  $: resolvedLabel = label ?? album?.title ?? '';
  $: iconPaths = album ? (ICON_PATHS[album.icon] ?? DEFAULT_ICON_PATHS) : DEFAULT_ICON_PATHS;
</script>

<a
  class="album-card"
  href={resolvedHref}
  style={size ? `width: ${size}; height: ${size};` : undefined}
>
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
  <h3>{resolvedLabel}</h3>
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
