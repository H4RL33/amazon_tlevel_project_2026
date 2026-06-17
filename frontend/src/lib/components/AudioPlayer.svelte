<!--
  AudioPlayer
  Purpose: Streams audio from a pre-signed S3 URL. Reports progress back to the API.
  Used in: ContentBlock (when content_type === 'audio').
  Props:
    - contentId (number): the Content item's id — used when calling updateProgress
    - src (string): pre-signed S3 URL for the audio file
  Behaviour:
    - Render an HTML <audio> element with controls.
    - On 'timeupdate' event: compute progress_pct = (currentTime / duration) * 100.
      Call updateProgress(contentId, Math.floor(progress_pct)) from $lib/api/progress.ts.
      Throttle: only call updateProgress when progress_pct changes by ≥ 5 points
      (track last reported value in a local variable).
    - On 'ended': call updateProgress(contentId, 100).
    - Show a ProgressBar below the audio element with the current progress_pct.
  Styling:
    width 100%, custom dark-themed audio controls if possible (see MDN for styling tips),
    ProgressBar below with pct bound to local progress_pct variable.
-->
<script lang="ts">
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let contentId: number;
  export let src: string;

  let progressPct = 0;
</script>

<!-- TODO: Implement audio element with timeupdate handler and ProgressBar. -->
