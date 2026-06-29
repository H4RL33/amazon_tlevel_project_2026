<!--
  AlbumProgressWidget
  Purpose: Widget pinned to the top-left of the screen while viewing an Album. Shows the
    Album's title and a smaller overall progress bar.
  Used in: Album view (e.g. /learn/[albumId])
  Props:
    - title (string): the Album's title
    - progressPct (number): overall completion percentage across all Snippets in the Album
  Layout:
    Flush with SnippetTitleBar (same height), title text then a thin ProgressBar below it.
  Styling:
    Background matches the Album view's top bar, ProgressBar fill in the orange-yellow gradient
    (override ProgressBar's default blue fill for this usage).
-->

<!-- Code may contain bugs or not run as expected-->
<script lang="ts">
  //< Changes ------------------------------------------------>

  import ProgressBar from '$lib/components/ProgressBar.svelte';
  // import the reusable ProgressBar component

  export let title: string;
  // Album title passed in by the parent component

  export let progressPct: number;
  // Overall completion percentage (0-100)
</script>

<!-- Main widget container -->
<div class="album-progress-widget">
  <!-- Display Album title -->
  <h2>{title}</h2>

  <!-- Show overall progress-->
  <ProgressBar value={progressPct} />
</div>

<!-- Changes ------------------------------------------------>

<!-- Code may contain bugs or not run as expected-->

<!-- TODO: Implement title + ProgressBar layout, pinned top-left, flush with SnippetTitleBar. -->

<style>
  /* Main container positioned at the top of the page */
  .album-progress-widget {
    position: sticky; /* Keeps the widget visible while scrolling */
    top: 0;
    left: 0;

    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.4rem;

    padding: 0.75rem 1rem;
    background: #1f1f1f;
    width: 100%;
    z-index: 10;
  }

  /* Album title styling */
  h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: white;
  }

  /* Make the progress bar thinner */
  :global(.progress-bar) {
    height: 4px;
  }

  /* Override the default progress bar colour */
  :global(.progress-fill) {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
  }
</style>
