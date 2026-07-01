<!--
  AlbumCard
  Purpose: Square icon-tile for Albums or Topics. In album mode (album prop set), links to
    /learn/[id] and shows album title + an enrol/unenrol toggle button for authenticated users.
    In topic mode (href + label set, no album), links to the provided href — no enrol button.
  Props:
    - album (AlbumListResponse | undefined): the Album to display. Optional.
    - href (string | undefined): overrides the link destination when set.
    - label (string | undefined): overrides the displayed title when set.
    - size (string | undefined): CSS size override (width and height), e.g. "100%".
    - icon (string | undefined): icon key (see ICON_PATHS) to use in href/label mode, since
      Topics have no icon field of their own. Ignored when album is set (album.icon wins).
-->
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';
  import { enrolAlbum, unenrolAlbum } from '$lib/api/albums';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
  import { currentUser } from '$lib/stores/user';

  export let album: AlbumListResponse | undefined = undefined;
  export let href: string | undefined = undefined;
  export let label: string | undefined = undefined;
  export let size: string | undefined = undefined;
  export let icon: string | undefined = undefined;

  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
    code: ['M9 8l-4 4 4 4', 'M15 8l4 4-4 4'],
    shield: ['M12 3l7 3v6c0 4.97-3.05 8.26-7 9c-3.95-.74-7-4.03-7-9V6z', 'M9 12l2 2 4-4'],
    globe: [
      'M12 21a9 9 0 100-18 9 9 0 000 18z',
      'M3 12h18M12 3c-2.4 3-2.4 15 0 18M12 3c2.4 3 2.4 15 0 18',
    ],
    chart: ['M5 20V13M12 20V6M19 20V10', 'M3 20h18'],
    briefcase: ['M3 8h18v11H3z', 'M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2M3 13h18'],
    heart: [
      'M12 20l-6.5-6.2C3 11.2 3 7.6 5.6 6.1a4.5 4.5 0 016.4 1.1 4.5 4.5 0 016.4-1.1c2.6 1.5 2.6 5.1.1 7.7z',
      'M4 13h3l2-3 2 5 2-4 1.5 2H20',
    ],
    building: ['M6 21V4h12v17H6z', 'M9 7v2M14 7v2M9 11v2M14 11v2M9 15v2M14 15v2'],
    compass: ['M12 21a9 9 0 100-18 9 9 0 000 18z', 'M15.5 8.5l-2.2 4.8-4.8 2.2 2.2-4.8z'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: resolvedHref = href ?? (album ? `/learn/${album.id}` : '/');
  $: resolvedLabel = label ?? album?.title ?? '';
  $: iconPaths = album
    ? (ICON_PATHS[album.icon] ?? DEFAULT_ICON_PATHS)
    : (ICON_PATHS[icon ?? ''] ?? DEFAULT_ICON_PATHS);
  $: albumId = album?.id;
  $: enrolled = albumId !== undefined ? $enrolledAlbumIds.has(albumId) : false;
  $: showToggle = !!$currentUser && albumId !== undefined;

  async function handleEnrolToggle(e: MouseEvent) {
    e.preventDefault();
    if (albumId === undefined) return;
    if (enrolled) {
      enrolledAlbumIds.update((s) => {
        s.delete(albumId!);
        return new Set(s);
      });
      await unenrolAlbum(albumId);
    } else {
      enrolledAlbumIds.update((s) => {
        s.add(albumId!);
        return new Set(s);
      });
      await enrolAlbum(albumId);
    }
  }
</script>

<div class="album-card" style={size ? `width: ${size}; height: ${size};` : undefined}>
  <a class="album-link" href={resolvedHref}>
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

  {#if showToggle}
    <button
      class="enrol-btn"
      class:enrolled
      on:click={handleEnrolToggle}
      aria-label={enrolled ? 'Remove from Library' : 'Add to Library'}
      title={enrolled ? 'Remove from Library' : 'Add to Library'}
    >
      {#if enrolled}
        <svg
          viewBox="0 0 24 24"
          width="14"
          height="14"
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
          width="14"
          height="14"
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

<style>
  .album-card {
    position: relative;
    display: flex;
    width: 190px;
    height: 190px;
    box-sizing: border-box;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
  }

  .album-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    width: 100%;
    height: 100%;
    padding: 1rem;
    text-decoration: none;
    color: inherit;
    box-sizing: border-box;
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
    font-family: 'Ubuntu', sans-serif;
  }

  .enrol-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    width: 22px;
    height: 22px;
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

  .enrol-btn:hover {
    background: #232f3e;
    color: #ffffff;
  }

  .enrol-btn.enrolled {
    background: #232f3e;
    color: #ffffff;
  }

  .enrol-btn.enrolled:hover {
    background: #ef4444;
    border-color: #ef4444;
    color: #ffffff;
  }
</style>
