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
  interface Album {
    id: number;
    title: string;
  }

  export let albums: Album[];
</script>

<!-- TODO: Render an AlbumCard per album. Show the empty state when albums.length === 0. -->
