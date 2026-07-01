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
  Hover: subtle cursor-following 3D tilt (via the `tilt` action — event-driven, transform-only,
    no continuous animation loop) plus a chromatic drop-shadow whose colours are derived from
    the current page's gradient backdrop palette (see getShadowHues in $lib/gradient). The
    plain->chromatic transition is a short one-shot "spin" (see chroma-spin keyframes below):
    box-shadow only, no filter, and it runs once (0.5s) rather than continuously, so it's a
    fundamentally different (much cheaper) animation than the always-on blur this app's perf
    pass found expensive elsewhere.
-->
<script lang="ts">
  import { page } from '$app/stores';
  import type { AlbumListResponse } from '$lib/api/types';
  import { enrolAlbum, unenrolAlbum } from '$lib/api/albums';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
  import { currentUser } from '$lib/stores/user';
  import { tilt } from '$lib/actions/tilt';
  import { getShadowHues, shadowHsl } from '$lib/gradient';

  const BASE_SHADOW = '0 10px 18px -4px rgba(35, 47, 62, 0.35)';

  function chromaShadow(hues: [number, number, number], spinOffset: number): string {
    const [a, b, c] = hues.map((h) => (h + spinOffset) % 360);
    return [
      BASE_SHADOW,
      `10px 14px 26px -8px ${shadowHsl(a, 0.35)}`,
      `-8px 14px 26px -8px ${shadowHsl(b, 0.3)}`,
      `0 20px 34px -12px ${shadowHsl(c, 0.25)}`,
    ].join(', ');
  }

  // spinStart is the plain shadow with no colour at all — the animation's own
  // first keyframe, not a CSS `transition`, handles the black->colour fade:
  // a `transition` on the same property never runs here because a running
  // `animation` always takes priority over it for that property while active.
  // The hue offset then decays from 80deg down to 0 so the shadow settles
  // exactly on the page's true palette by the end of the spin.
  $: hues = getShadowHues($page.url.pathname);
  $: spinStart = BASE_SHADOW;
  $: spinPhase0 = chromaShadow(hues, 80);
  $: spinPhase1 = chromaShadow(hues, 45);
  $: spinPhase2 = chromaShadow(hues, 15);
  $: spinPhase3 = chromaShadow(hues, 0);

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

<div
  class="album-card"
  use:tilt
  style="{size
    ? `width: ${size}; height: ${size};`
    : ''} --phase-start: {spinStart}; --phase-0: {spinPhase0}; --phase-1: {spinPhase1}; --phase-2: {spinPhase2}; --phase-3: {spinPhase3};"
>
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
    width: 100%;
    aspect-ratio: 1;
    box-sizing: border-box;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    /* box-shadow-only transition (no filter, no continuous animation) — cheap
       to run once on hover in/out, unlike the always-on animated blur this
       app's perf pass found expensive elsewhere. */
    transition: box-shadow 0.3s ease;
    transform-style: preserve-3d;
  }

  .album-card:hover {
    animation: chroma-spin 0.6s ease-in-out forwards;
  }

  @keyframes chroma-spin {
    0% {
      box-shadow: var(--phase-start);
    }
    25% {
      box-shadow: var(--phase-0);
    }
    55% {
      box-shadow: var(--phase-1);
    }
    80% {
      box-shadow: var(--phase-2);
    }
    100% {
      box-shadow: var(--phase-3);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .album-card {
      transition: none;
    }

    .album-card:hover {
      animation: none;
      box-shadow: var(--phase-3);
    }
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
    border: none;
    border-radius: 0;
    cursor: pointer;
    color: #232f3e;
    padding: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
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
    color: #ffffff;
  }
</style>
