<!--
  ProgressBar
  Purpose: Thin horizontal bar showing reading or listening completion.
  Used in: AudioPlayer, VideoPlayer, AlbumCard, AlbumProgressWidget, EnrolledAlbumsList.
  Props:
    - pct (number): completion percentage, 0–100
  Styling:
    height 4px, border-radius 2px, background-track #21262d,
    background-fill #1f6feb, width of fill = pct%
    Do not show label text — the bar is purely visual.
-->
<script lang="ts">
  export let pct: number;
</script>

<!-- TODO: Implement progress bar. Clamp pct to 0–100 before applying width. -->
