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
    background #0a2540, full height, width 240px, padding 1rem 0.75rem,
    text-primary #c9d1d9, text-muted #8b949e, font-size 0.875rem
    Active link: bold, accent_colour left border, background rgba(31,111,235,0.1)
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';

  export let topics: TopicResponse[];
  export let activePath: string;
</script>

<nav class="sidebar">
  {#each topics as topic}
    <a href={`/topics/${topic.slug}`} class:active={activePath.startsWith(`/topics/${topic.slug}`)}>
      {topic.name}
    </a>
  {/each}
</nav>

<style>
  .sidebar {
    background: #0a2540;
    height: 100%;
    width: 240px;
    padding: 1rem 0.75rem;
  }

  a {
    color: #c9d1d9;
    text-decoration: none;
    font-size: 0.875rem;
    padding: 0.5rem 0;
    display: block;
  }

  a:hover,
  a.active {
    background-color: rgba(31, 111, 235, 0.1);
    border-left: 3px solid #1f6ffb;
    font-weight: bold;
  }
</style>
