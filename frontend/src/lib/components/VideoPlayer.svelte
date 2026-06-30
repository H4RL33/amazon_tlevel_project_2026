<!--
  VideoPlayer
  Purpose: Plays video from a pre-signed S3 URL. Reports progress to the API.
  Used in: Snippet reading view (when content_type === 'video').
  Props:
    - contentId (number): the Content item's id
    - src (string): pre-signed S3 URL for the video file
  Behaviour:
    - On 'timeupdate': compute and throttle updateProgress calls (every 5 pct points).
    - On 'ended': call updateProgress(contentId, 100).
    - Provide custom play/pause, 10s skip back/forward controls, and a progress bar.
-->


<script lang="ts">

// think it is better to use defaut Html one but this contains the code for a basic video player
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let contentId: number;
  export let src: string;

  let videoElement: HTMLVideoElement | null = null;
  let progressPct = 0;
  let currentTime = 0;
  let duration = 0;
  let isPlaying = false;
  let lastReported = 0;

  function formatTime(seconds: number) {
    if (!Number.isFinite(seconds)) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  async function handleTimeUpdate(event: Event) {
    const video = event.currentTarget as HTMLVideoElement;
    if (!video.duration) return;

    currentTime = video.currentTime;
    duration = video.duration;
    progressPct = Math.floor((video.currentTime / video.duration) * 100);

    if (progressPct - lastReported >= 5) {
      lastReported = progressPct;

      try {
        await updateProgress(contentId, progressPct);
      } catch (err) {
        console.error('Failed to update video progress:', err);
      }
    }
  }

  async function handleEnded() {
    progressPct = 100;
    currentTime = duration;
    isPlaying = false;

    try {
      await updateProgress(contentId, 100);
    } catch (err) {
      console.error('Failed to update completion:', err);
    }
  }

  function handleLoadedMetadata() {
    if (!videoElement) return;
    duration = videoElement.duration || 0;
    currentTime = videoElement.currentTime || 0;
  }

  function togglePlayback() {
    if (!videoElement) return;

    if (videoElement.paused) {
      void videoElement.play();
      isPlaying = true;
    } else {
      videoElement.pause();
      isPlaying = false;
    }
  }

  function skipBy(seconds: number) {
    if (!videoElement) return;

    const nextTime = Math.max(0, Math.min(videoElement.duration || 0, videoElement.currentTime + seconds));
    videoElement.currentTime = nextTime;
    currentTime = nextTime;
  }

  function handleSeek(pct: number) {
    if (!videoElement) return;

    const nextTime = (pct / 100) * duration;
    videoElement.currentTime = nextTime;
    currentTime = nextTime;
    progressPct = pct;
  }
</script>

<div class="video-player">
  <div class="video-frame">
    <video
      bind:this={videoElement}
      {src}
      preload="metadata"
      playsinline
      on:loadedmetadata={handleLoadedMetadata}
      on:timeupdate={handleTimeUpdate}
      on:play={() => (isPlaying = true)}
      on:pause={() => (isPlaying = false)}
      on:ended={handleEnded}
    />
  </div>

  <div class="controls">
    <button type="button" class="control-button" on:click={() => skipBy(-10)} aria-label="Skip backward 10 seconds">
      ⏪ 10s
    </button>
    <button type="button" class="control-button primary" on:click={togglePlayback} aria-label={isPlaying ? 'Pause video' : 'Play video'}>
      {#if isPlaying}⏸ Pause{:else}▶ Play{/if}
    </button>
    <button type="button" class="control-button" on:click={() => skipBy(10)} aria-label="Skip forward 10 seconds">
      10s ⏩
    </button>
  </div>

  <div class="timeline">
    <span>{formatTime(currentTime)}</span>
    <ProgressBar pct={progressPct} onSeek={handleSeek} />
    <span>{formatTime(duration)}</span>
  </div>
</div>

<style>
  .video-player {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: 100%;
  }

  .video-frame {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    border-radius: 12px;
    overflow: hidden;
  }

  video {
    display: block;
    width: 100%;
    height: 100%;
    background: #000;
  }

  .controls {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .control-button {
    border: 0;
    border-radius: 999px;
    padding: 0.6rem 1rem;
    font-weight: 600;
    color: #f8fafc;
    background: #334155;
    cursor: pointer;
  }

  .control-button.primary {
    background: #2563eb;
  }

  .timeline {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.75rem;
    color: #cbd5e1;
    font-size: 0.9rem;
  }
</style>
