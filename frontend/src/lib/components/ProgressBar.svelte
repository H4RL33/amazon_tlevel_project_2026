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
  import { draw } from 'svelte/transition';

  //max-length is how many pixels long  the progress bar is at 100%
  let max_length = 100;
  pct = 0;
</script>

<svg viewBox="0 0 200 200" version="1.1">
  <!-- creates a larger black bar behind the blue bar to show the progress -->
  <line x1="0" y1="100" x2={max_length} y2="100" stroke="#21262d" stroke-width="12" />

  <!-- creates a blue bar that is the length of the percentage of the max-length -->
  <line x1="0" y1="100" x2={(max_length * pct) / 100} y2="100" stroke="#1f6feb" stroke-width="10" />
</svg>
<!-- TODO: Implement progress bar. Clamp pct to 0–100 before applying width. -->
