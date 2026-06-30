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
<script lang="ts">
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let title: string;
  export let progressPct: number;
</script>

<!-- TODO: Implement title + ProgressBar layout, pinned top-left, flush with SnippetTitleBar. -->
