<!--
  EnrolledAlbumsList
  Purpose: List of the user's enrolled AlbumCards with progress, shown in The Library.
  Used in: /library
  Props:
    - albums (Array<{ album: Album; progress: number }> — TODO: replace Album with the real
      API type once the Album model and an `/albums/enrolled` endpoint exist)
  Behaviour:
    If albums is empty, show an empty state: "You haven't enrolled in any Albums yet —
    browse Albums to get started."
  Styling:
    Vertical list of AlbumCards, gap 1rem.
-->
<script lang="ts">
  interface Album {
    id: number;
    title: string;
  }

  export let albums: Array<{ album: Album; progress: number }>;
</script>

<!-- TODO: Render an AlbumCard per entry (passing progress). Show the empty state when albums.length === 0. -->
