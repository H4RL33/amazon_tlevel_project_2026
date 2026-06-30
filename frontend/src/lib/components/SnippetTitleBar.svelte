<!--
  SnippetTitleBar
  Purpose: Top title bar shown while reading a Snippet within an Album. Same height as, and
    flush with, AlbumProgressWidget. Displays the current Snippet's title and a dynamic
    reading-progress bar along the bottom edge.
  Used in: Album view, Snippet reading view
  Props:
    - title (string): the current Snippet's title
    - progressPct (number): the user's reading progress through this Snippet (0–100)
  Layout:
    Title text, full-width, with a thin progress bar along the bottom edge of the bar itself
    (not below it — the bar IS the bottom border).
  Styling:
    Height matches AlbumProgressWidget. Bottom progress bar in the orange-yellow gradient.
-->
<script lang="ts">
  // Title of the current snippet being read
  export let title: string;

  // Reading progress (0–100)
  export let progressPct: number;
</script>

<!-- Title bar container -->
<div class="title-bar">
  <!-- Snippet title -->
  <span class="title">{title}</span>

  <!-- Progress bar sits INSIDE the bottom edge -->
  <div class="progress-track">
    <div class="progress-fill" style="width: {progressPct}%" />
  </div>
</div>
<!-- TODO: Implement title bar with a bottom-edge progress indicator (orange-yellow gradient). -->

<style>
  /* Main bar container */
  .title-bar {
    position: relative;
    display: flex;
    align-items: center;

    /* adjust this to match AlbumProgressWidget height */
    height: 56px;

    padding: 0 1rem;
    background: #111; /* adjust to your design */
    color: white;
  }

  /* Title text */
  .title {
    font-size: 1rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Thin track pinned to bottom edge */
  .progress-track {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 4px;

    background: rgba(255, 255, 255, 0.1);
  }

  /* Actual progress fill */
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #ff8a00, #ffd000); /* orange → yellow gradient */

    transition: width 0.2s ease;
  }
</style>
