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
    used everywhere else in this layout. Columns are auto-fit minmax(190px, 1fr) so that
    however many 190px+ columns actually fit the container width, they stretch evenly to
    consume the full row with no dangling space on the right — auto-fit (rather than
    auto-fill) is used deliberately so that when there are fewer albums than would fill a
    row, the empty tracks collapse and the real cards expand to fill the row instead of
    leaving a blank gap where unused tracks would otherwise sit.
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
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--gap-inner);
  }
</style>
