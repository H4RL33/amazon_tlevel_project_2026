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
  import type { AlbumListResponse } from '$lib/api/types';
  import AlbumCard from '$lib/components/AlbumCard.svelte';

  // This prop holds the albums the user has enrolled in, plus each album's progress.
  export let albums: Array<{ album: AlbumListResponse; progress: number }>;
</script>

{#if albums.length === 0}
  <!-- Show a friendly message when the user has not enrolled in anything yet. -->
  <p class="empty-state">
    You haven't enrolled in any Albums yet — browse Albums to get started.
  </p>
{:else}
  <!-- Render each enrolled album as a card and show how far the user has progressed. -->
  <div class="album-list">
    {#each albums as item}
      <div class="album-item">
        <AlbumCard album={item.album} />
        <p class="progress">Progress: {item.progress}%</p>
      </div>
    {/each}
  </div>
{/if}

<style>
  .album-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .album-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .empty-state {
    margin: 0;
    color: #4b5563;
  }

  .progress {
    margin: 0;
    color: #374151;
    font-size: 0.95rem;
  }
</style>
