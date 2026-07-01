<!--
  TopicBanner
  Purpose: Wide rectangular "banner" tile for a Topic on the /t-levels index page.
    Deliberately distinct from AlbumCard's square tile shape so Topics/T-Levels read as a
    different kind of thing from Albums at a glance: left-aligned icon, title + description
    stacked to its right, vertically centred as a group.
  Props:
    - topic (TopicResponse): the Topic to render (name, description, slug).
    - icon (string | undefined): icon key (see ICON_PATHS below) — same vocabulary subset
      used by AlbumCard for the icons this page actually needs (code, briefcase, cloud,
      compass, heart). Duplicated here (not imported) because AlbumCard.svelte is owned by
      another workstream and is out of bounds to edit/refactor for this task.
  Hover: subtle cursor-following 3D tilt (via the `tilt` action) plus a chromatic drop-shadow
    derived from the current page's gradient backdrop palette, fading/spinning in via a short
    one-shot box-shadow keyframe animation (see chroma-spin below) — ported from AlbumCard's
    identical pattern, no filter, no continuous loop.
-->
<script lang="ts">
  import { page } from '$app/stores';
  import type { TopicResponse } from '$lib/api/types';
  import { tilt } from '$lib/actions/tilt';
  import { getShadowHues, shadowHsl } from '$lib/gradient';

  export let topic: TopicResponse;
  export let icon: string | undefined = undefined;

  // Small subset of AlbumCard's ICON_PATHS — only the keys TOPIC_ICONS in
  // +page.svelte actually uses. Same monochrome line-art style (24x24 viewBox).
  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
    code: ['M9 8l-4 4 4 4', 'M15 8l4 4-4 4'],
    briefcase: ['M3 8h18v11H3z', 'M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2M3 13h18'],
    heart: [
      'M12 20l-6.5-6.2C3 11.2 3 7.6 5.6 6.1a4.5 4.5 0 016.4 1.1 4.5 4.5 0 016.4-1.1c2.6 1.5 2.6 5.1.1 7.7z',
      'M4 13h3l2-3 2 5 2-4 1.5 2H20',
    ],
    compass: ['M12 21a9 9 0 100-18 9 9 0 000 18z', 'M15.5 8.5l-2.2 4.8-4.8 2.2 2.2-4.8z'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

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
  // first keyframe, not a CSS `transition`, handles the black->colour fade (see
  // AlbumCard.svelte for the full rationale). The hue offset decays from 80deg
  // down to 0 so the shadow settles exactly on the page's true palette by the
  // end of the spin.
  $: hues = getShadowHues($page.url.pathname);
  $: spinStart = BASE_SHADOW;
  $: spinPhase0 = chromaShadow(hues, 80);
  $: spinPhase1 = chromaShadow(hues, 45);
  $: spinPhase2 = chromaShadow(hues, 15);
  $: spinPhase3 = chromaShadow(hues, 0);

  $: iconPaths = ICON_PATHS[icon ?? ''] ?? DEFAULT_ICON_PATHS;
</script>

<a
  class="topic-banner"
  href="/t-levels/{topic.slug}"
  use:tilt
  style="--phase-start: {spinStart}; --phase-0: {spinPhase0}; --phase-1: {spinPhase1}; --phase-2: {spinPhase2}; --phase-3: {spinPhase3};"
>
  <span class="icon-wrap">
    <svg
      class="icon"
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="34"
      height="34"
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
  </span>
  <span class="text">
    <h3>{topic.name}</h3>
    <p>{topic.description}</p>
  </span>
</a>

<style>
  .topic-banner {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    width: 100%;
    max-width: 600px;
    box-sizing: border-box;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    padding: 1rem 1.5rem;
    text-decoration: none;
    color: inherit;
    overflow: hidden;
    /* box-shadow-only transition (no filter, no continuous animation) — the
       `tilt` action owns `transform` directly, so it isn't listed here to
       avoid two systems fighting over the same property. */
    transition: box-shadow 0.3s ease;
    transform-style: preserve-3d;
  }

  .topic-banner:hover {
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
    .topic-banner {
      transition: none;
    }

    .topic-banner:hover {
      animation: none;
      box-shadow: var(--phase-3);
    }
  }

  .icon-wrap {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    margin-left: 0.5rem;
    background: #f5f5f0;
  }

  .text {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.3rem;
    min-width: 0;
  }

  h3 {
    margin: 0;
    color: #232f3e;
    font-size: 1.05rem;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  p {
    margin: 0;
    color: #5a6472;
    font-size: 0.85rem;
    font-family: 'Ubuntu', sans-serif;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
