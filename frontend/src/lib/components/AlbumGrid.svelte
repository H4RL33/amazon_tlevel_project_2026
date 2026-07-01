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
-->
<script lang="ts">
  import AlbumCard from './AlbumCard.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let albums: AlbumListResponse[];
</script>

{#if albums.length === 0}
  <p>No Albums available yet.</p>
{:else}
  <div class="album-grid">
    {#each albums as album}
      <!-- Code above goes through every item in the albums array, and for each item, calls it album -->
      <AlbumCard {album} />
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
