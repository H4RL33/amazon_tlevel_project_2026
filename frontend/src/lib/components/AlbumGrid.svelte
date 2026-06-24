<!--
  AlbumGrid
  Purpose: Grid/list of AlbumCards for browsing all available Albums. Publicly viewable without
    an account (enrolling requires one, via EnrolButton on the Album view itself).
  Used in: Album discovery page
  Props:
    - albums (Album[] — TODO: replace with real API type once the Album model exists; same
      shape AlbumCard expects)
  Behaviour:
    If albums is empty, show an empty state: "No Albums available yet."
  Styling:
    CSS grid, responsive columns (e.g. repeat(auto-fill, minmax(280px, 1fr))), gap 1rem.
-->
<script lang="ts">
  /* Changes */
  import AlbumCard from './AlbumCard.svelte';
  // Album card data 
  interface Album {
    id: number;
    title: string;
    tagline: string;
    iconUrl: string;
    snippetCount: number;
  }
 // Album card data 
  export let albums: Album[];
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
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }
</style>
<!-- Changes -->

<!-- TODO: Render an AlbumCard per album. Show the empty state when albums.length === 0. -->
