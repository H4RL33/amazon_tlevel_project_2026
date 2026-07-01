<!--
  SnippetCard
  Props:
    - content: object with id, title, content_type
    - xp (number | undefined): XP shown via badge if set
    - saved (boolean | undefined): whether saved to library
    - onSaveToggle (() => void | undefined): called on save button click
  Hover: subtle cursor-following 3D tilt (via the `tilt` action) plus a chromatic
    drop-shadow derived from the current page's gradient backdrop palette, fading/spinning
    in via a short one-shot box-shadow keyframe animation (see chroma-spin below) — no
    filter, no continuous loop.
-->
<script lang="ts">
  import { page } from '$app/stores';
  import { tilt } from '$lib/actions/tilt';
  import { getShadowHues, shadowHsl } from '$lib/gradient';

  export let content: { id: number; title: string; content_type: string };
  export let xp: number | undefined = undefined;
  export let saved: boolean | undefined = undefined;
  export let onSaveToggle: (() => void) | undefined = undefined;

  const ICONS: Record<string, string> = {
    article: '📄',
    audio: '🎧',
    video: '🎬',
  };

  const BASE_SHADOW = '0 4px 14px rgba(35, 47, 62, 0.18)';

  function chromaShadow(hues: [number, number, number], spinOffset: number): string {
    const [a, b, c] = hues.map((h) => (h + spinOffset) % 360);
    return [
      BASE_SHADOW,
      `8px 10px 20px -6px ${shadowHsl(a, 0.35)}`,
      `-6px 10px 20px -6px ${shadowHsl(b, 0.3)}`,
      `0 16px 26px -10px ${shadowHsl(c, 0.25)}`,
    ].join(', ');
  }

  $: icon = ICONS[content.content_type] ?? '📄';
  $: hues = getShadowHues($page.url.pathname);
  $: spinPhase0 = chromaShadow(hues, 80);
  $: spinPhase1 = chromaShadow(hues, 45);
  $: spinPhase2 = chromaShadow(hues, 15);
  $: spinPhase3 = chromaShadow(hues, 0);
</script>

<div
  class="snippet-card"
  use:tilt
  style="--phase-0: {spinPhase0}; --phase-1: {spinPhase1}; --phase-2: {spinPhase2}; --phase-3: {spinPhase3};"
>
  {#if xp !== undefined}
    <span class="xp-badge">+{xp} XP</span>
  {/if}
  {#if onSaveToggle !== undefined}
    <button
      class="save-btn"
      class:saved
      on:click|stopPropagation={onSaveToggle}
      aria-label={saved ? 'Remove from library' : 'Save to library'}
      title={saved ? 'Remove from library' : 'Save to library'}
    >
      {#if saved}
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
  <span class="icon" aria-hidden="true">{icon}</span>
  <span class="title">{content.title}</span>
</div>

<style>
  .snippet-card {
    position: relative;
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(35, 47, 62, 0.12);
    cursor: pointer;
    /* box-shadow-only transition — the `tilt` action owns `transform` directly
       (see $lib/actions/tilt), so it isn't listed here to avoid two systems
       fighting over the same property. */
    transition: box-shadow 0.3s ease;
    transform-style: preserve-3d;
  }

  .snippet-card:hover {
    animation: chroma-spin 0.5s ease-out forwards;
  }

  @keyframes chroma-spin {
    0% {
      box-shadow: var(--phase-0);
    }
    35% {
      box-shadow: var(--phase-1);
    }
    70% {
      box-shadow: var(--phase-2);
    }
    100% {
      box-shadow: var(--phase-3);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .snippet-card {
      transition: none;
    }

    .snippet-card:hover {
      animation: none;
      box-shadow: var(--phase-3);
    }
  }

  .icon {
    font-size: 2rem;
  }

  .title {
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    color: #232f3e;
    line-height: 1.3;
  }

  .xp-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    font-size: 0.7rem;
    font-weight: 700;
    background: linear-gradient(to right, #f97316, #facc15);
    color: white;
    border-radius: 99px;
    padding: 0.15rem 0.45rem;
  }

  .save-btn {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
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

  .save-btn:hover {
    background: #232f3e;
    color: #ffffff;
  }

  .save-btn.saved {
    background: #232f3e;
    color: #ffffff;
  }

  .save-btn.saved:hover {
    background: #ef4444;
    color: #ffffff;
  }
</style>
