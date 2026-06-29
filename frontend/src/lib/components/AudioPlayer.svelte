<!--
  AudioPlayer
  Purpose: Streams audio from a pre-signed S3 URL. Reports progress back to the API.
  Used in: Snippet reading view (when content_type === 'audio').
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

<!-- Code may contain bugs or be incomplete, may need updating. -->
<!-- Changes ----------------------------------------------->
<!-- Template ---------------------------------------------->

<script lang="ts">
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  // ID of the content item whose progress should be updated.
  export let contentId: number;
  // Pre-signed S3 URL of the audio file.
  export let src: string;

  // Current playback progress (0–100).
  let progressPct = 0;

  // Last progress value sent to the API.
  // Used to avoid sending a request on every timeupdate event.
  let lastReported = 0;

  /**
   * Updates the progress percentage while the audio is playing.
   * Sends progress updates to the API every 5%.
   */
  async function handleTimeUpdate(event: Event) {
    const audio = event.currentTarget as HTMLAudioElement;
    // Prevent division by zero before the audio metadata has loaded.
    if (!audio.duration) return;

    // Calculate playback progress as a whole percentage.
    progressPct = Math.floor((audio.currentTime / audio.duration) * 100);

    // Only report progress every 5%.
    if (progressPct - lastReported >= 5) {
      lastReported = progressPct;

      try {
        await updateProgress(contentId, progressPct);
      } catch (err) {
        console.error('Failed to update progress:', err);
      }
    }
  }

  /**
   * Marks the audio as fully completed when playback ends.
   */
  async function handleEnded() {
    progressPct = 100;

    try {
      await updateProgress(contentId, 100);
    } catch (err) {
      console.error('Failed to update completion:', err);
    }
  }
</script>

<!-- HTML audio player -->
<audio controls {src} on:timeupdate={handleTimeUpdate} on:ended={handleEnded} />

<!-- Template ---------------------------------------------->
<!-- Changes ----------------------------------------------->
<!-- Code may contain bugs or be incomplete, may need updating. -->

<style>
  audio {
    width: 100%;
    margin-bottom: 1rem;
  }

  /* Basic dark theme.
     Browser support for styling native controls varies. */
  audio {
    background: #1f2937;
    border-radius: 8px;
  }
</style>
