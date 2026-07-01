<!--
  AlbumGrid
  Purpose: Grid/list of AlbumCards for browsing all available Albums. Publicly viewable without
    an account (enrolling requires one, via EnrolButton on the Album view itself).
  Used in: Album discovery page
  Props:
    - albums (AlbumListResponse[]): same shape AlbumCard expects
  Behaviour:
    If albums is empty, show an empty state: "No Albums available yet."
  Styling:
    CSS grid of square AlbumCard tiles, gap matches the global --gap-inner spacing token
    used everywhere else in this layout. Columns are auto-fit minmax(190px, 220px): auto-fit
    (rather than auto-fill) collapses empty tracks so a full row of cards stretches evenly
    to consume the width with no dangling gap on the right, but the 220px upper bound stops
    that stretch from running away — this component is also used per-topic-section on
    /learn and /t-levels/[slug], where a section can have as few as 1-2 albums, and an
    unbounded 1fr (tried first, then reverted) let those sparse sections stretch a single
    card to the full container width.
  Motion:
    Cards fade/slide in with a small per-index stagger on first render (one-shot entrance,
    not a continuous animation — safe under this app's "no animated filter + continuous
    transform" perf constraint). The wrapper div around each AlbumCard carries the
    `in:fly` transition rather than AlbumCard itself, since AlbumCard is owned by other
    work landed today; the wrapper has no layout styles of its own so it doesn't disturb
    the grid track sizing (AlbumCard's own width:100%/aspect-ratio:1 still determines the
    cell's rendered size). Stagger delay is capped so grids with many albums don't take
    seconds for the last card to appear. Respects prefers-reduced-motion by zeroing the
    duration/delay, matching the detection approach used in +layout.svelte. Uses the
    `|global` transition modifier: this each-block sits inside the parent's
    `{#if albums.length === 0}/{:else}` conditional, so the block that's actually being
    "introduced" (in Svelte's transition-locality sense) is the {:else} branch, not the
    each-block itself — a plain (local) `in:fly` here is silently skipped by Svelte 4
    because the each-block wasn't the block directly toggled. `|global` makes the intro
    play regardless of which ancestor block triggered the mount.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import AlbumCard from './AlbumCard.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let albums: AlbumListResponse[];

  const STAGGER_STEP_MS = 40;
  const STAGGER_CAP_MS = 400;

  // Read synchronously (not inside onMount) since entrance() can be evaluated by Svelte's
  // transition machinery before this component's onMount callback runs (e.g. when this
  // whole grid mounts as part of a reactive update once album data arrives) — reading it
  // only inside onMount raced the transition and reduced motion was silently ignored.
  // Safe because this app disables SSR (`export const ssr = false` in +layout.ts), so
  // `window` is always defined here; guarded anyway for defensiveness.
  let reduceMotion =
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  onMount(() => {
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      reduceMotion = e.matches;
    };
    reducedMotionQuery.addEventListener('change', handleChange);
    return () => reducedMotionQuery.removeEventListener('change', handleChange);
  });

  function entrance(i: number) {
    if (reduceMotion) return { duration: 0 };
    return { y: 12, duration: 250, delay: Math.min(i * STAGGER_STEP_MS, STAGGER_CAP_MS) };
  }
</script>

{#if albums.length === 0}
  <p>No Albums available yet.</p>
{:else}
  <div class="album-grid">
    {#each albums as album, i (album.id)}
      <!-- Code above goes through every item in the albums array, and for each item, calls it album -->
      <div in:fly|global={entrance(i)}>
        <AlbumCard {album} />
      </div>
      <!-- Code above is shorthand for <AlbumCard album={album} /> -->
    {/each}
  </div>
{/if}

<style>
  .album-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 220px));
    gap: var(--gap-inner);
  }
</style>
