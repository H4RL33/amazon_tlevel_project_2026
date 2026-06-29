<!--
  SnippetCard
  Props:
    - content: object with id, title, content_type
    - xp (number | undefined): XP shown via badge if set
    - saved (boolean | undefined): whether saved to library
    - onSaveToggle (() => void | undefined): called on save button click
-->
<script lang="ts">
  export let content: { id: number; title: string; content_type: string };
  export let xp: number | undefined = undefined;
  export let saved: boolean | undefined = undefined;
  export let onSaveToggle: (() => void) | undefined = undefined;

  const ICONS: Record<string, string> = {
    article: '📄',
    audio: '🎧',
    video: '🎬',
  };

  $: icon = ICONS[content.content_type] ?? '📄';
</script>

<div class="snippet-card">
  {#if xp !== undefined}
    <span class="xp-badge">+{xp} XP</span>
  {/if}
  {#if onSaveToggle !== undefined}
    <button
      class="save-btn"
      class:saved
      on:click|stopPropagation={onSaveToggle}
      aria-label={saved ? 'Remove from library' : 'Save to library'}
      title={saved ? 'Remove from library' : 'Save to library'}
    >
      {saved ? '🔖' : '🏷️'}
    </button>
  {/if}
  <span class="icon" aria-hidden="true">{icon}</span>
  <span class="title">{content.title}</span>
</div>

<style>
  .snippet-card {
    position: relative;
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(35, 47, 62, 0.12);
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .snippet-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(35, 47, 62, 0.18);
  }

  .icon {
    font-size: 2rem;
  }

  .title {
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    color: #232f3e;
    line-height: 1.3;
  }

  .xp-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    font-size: 0.7rem;
    font-weight: 700;
    background: linear-gradient(to right, #f97316, #facc15);
    color: white;
    border-radius: 99px;
    padding: 0.15rem 0.45rem;
  }

  .save-btn {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    line-height: 1;
    opacity: 0.6;
    transition: opacity 0.15s;
  }

  .save-btn:hover,
  .save-btn.saved {
    opacity: 1;
  }
</style>
