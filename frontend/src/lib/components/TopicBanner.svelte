<!--
  TopicBanner
  Purpose: Wide rectangular "banner" tile for a Topic on the /t-levels index page.
    Deliberately distinct from AlbumCard's square tile shape so Topics/T-Levels read as a
    different kind of thing from Albums at a glance: left-aligned icon, title + description
    stacked to its right, vertically centred as a group, thin accent-colour edge on the left.
  Props:
    - topic (TopicResponse): the Topic to render (name, description, accent_colour, slug).
    - icon (string | undefined): icon key (see ICON_PATHS below) — same vocabulary subset
      used by AlbumCard for the icons this page actually needs (code, briefcase, cloud,
      compass, heart). Duplicated here (not imported) because AlbumCard.svelte is owned by
      another workstream and is out of bounds to edit/refactor for this task.
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';

  export let topic: TopicResponse;
  export let icon: string | undefined = undefined;

  // Small subset of AlbumCard's ICON_PATHS — only the keys TOPIC_ICONS in
  // +page.svelte actually uses. Same monochrome line-art style (24x24 viewBox).
  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
    code: ['M9 8l-4 4 4 4', 'M15 8l4 4-4 4'],
    briefcase: ['M3 8h18v11H3z', 'M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2M3 13h18'],
    heart: [
      'M12 20l-6.5-6.2C3 11.2 3 7.6 5.6 6.1a4.5 4.5 0 016.4 1.1 4.5 4.5 0 016.4-1.1c2.6 1.5 2.6 5.1.1 7.7z',
      'M4 13h3l2-3 2 5 2-4 1.5 2H20',
    ],
    compass: ['M12 21a9 9 0 100-18 9 9 0 000 18z', 'M15.5 8.5l-2.2 4.8-4.8 2.2 2.2-4.8z'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: iconPaths = ICON_PATHS[icon ?? ''] ?? DEFAULT_ICON_PATHS;
</script>

<a class="topic-banner" href="/t-levels/{topic.slug}" style="--accent: {topic.accent_colour}">
  <span class="accent-bar" />
  <span class="icon-wrap">
    <svg
      class="icon"
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="34"
      height="34"
      fill="none"
      stroke="#232f3e"
      stroke-width="1.3"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      {#each iconPaths as d}
        <path {d} />
      {/each}
    </svg>
  </span>
  <span class="text">
    <h3>{topic.name}</h3>
    <p>{topic.description}</p>
  </span>
</a>

<style>
  .topic-banner {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    width: 100%;
    max-width: 600px;
    box-sizing: border-box;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    padding: 1rem 1.5rem;
    text-decoration: none;
    color: inherit;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
  }

  .topic-banner:hover {
    box-shadow: 0 14px 24px -6px rgba(35, 47, 62, 0.45);
  }

  .accent-bar {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 6px;
    background: var(--accent, #232f3e);
  }

  .icon-wrap {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    margin-left: 0.5rem;
    background: color-mix(in srgb, var(--accent, #232f3e) 12%, transparent);
  }

  .text {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.3rem;
    min-width: 0;
  }

  h3 {
    margin: 0;
    color: #232f3e;
    font-size: 1.05rem;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  p {
    margin: 0;
    color: #5a6472;
    font-size: 0.85rem;
    font-family: 'Ubuntu', sans-serif;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
