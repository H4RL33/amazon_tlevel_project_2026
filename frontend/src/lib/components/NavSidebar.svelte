<!--
  NavSidebar
  Purpose: Topic-list section nav, used inline within pages that need to browse by
    Topic (e.g. /topics, /learn) -- not a persistent global app sidebar. Global nav
    (Library/Dashboard/avatar) lives in Navbar/NavBarAvatar instead.
  Used in: /topics, /learn (wired up in a later chapter)
  Props:
    - topics (TopicResponse[]): list of all 5 topics to render as nav links
    - activePath (string): current URL path -- highlight matching topic link
  Layout:
    Topic links -> /topics/[slug] for each topic.
  Styling:
    Floating white PageCard (aside), 288px wide, full height of its row, sticky inner
    nav content -- same treatment as AlbumSidebar.
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';
  import PageCard from '$lib/components/PageCard.svelte';

  export let topics: TopicResponse[];
  export let activePath: string;
</script>

<PageCard as="aside" width="288px" padding="1.5rem 1rem">
  <nav class="sidebar">
    {#each topics as topic}
      <a
        href={`/topics/${topic.slug}`}
        class:active={activePath.startsWith(`/topics/${topic.slug}`)}
      >
        {topic.name}
      </a>
    {/each}
  </nav>
</PageCard>

<style>
  .sidebar {
    position: sticky;
    top: var(--gap-inner);
  }

  a {
    color: #232f3e;
    text-decoration: none;
    font-size: 0.875rem;
    padding: 0.5rem 0;
    display: block;
  }

  a:hover,
  a.active {
    background-color: rgba(31, 111, 235, 0.08);
    border-left: 3px solid #1f6ffb;
    font-weight: bold;
  }
</style>
