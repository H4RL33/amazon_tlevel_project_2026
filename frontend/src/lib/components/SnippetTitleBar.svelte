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
  export let title: string;
  export let progressPct: number;
</script>

<!-- TODO: Implement title bar with a bottom-edge progress indicator (orange-yellow gradient). -->
