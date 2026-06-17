<!--
  VideoPlayer
  Purpose: Plays video from a pre-signed S3 URL. Reports progress to the API.
  Used in: ContentBlock (when content_type === 'video').
  Props:
    - contentId (number): the Content item's id
    - src (string): pre-signed S3 URL for the video file
  Behaviour:
    Identical progress reporting pattern to AudioPlayer:
    - On 'timeupdate': compute and throttle updateProgress calls (every 5 pct points).
    - On 'ended': call updateProgress(contentId, 100).
    - Show ProgressBar below the video.
  Styling:
    16:9 aspect ratio container (padding-top: 56.25%, position relative),
    <video> fills the container (position absolute, top 0, left 0, width 100%, height 100%),
    controls attribute enabled, background #000.
    ProgressBar below the aspect-ratio container.
-->
<script lang="ts">
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let contentId: number;
  export let src: string;

  let progressPct = 0;
</script>

<!-- TODO: Implement 16:9 video container with timeupdate handler and ProgressBar. -->
