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
    export let items = [
        { label: "Home", href: "/" },
        { label: "About", href: "/about" },
        { label: "Contact", href: "/contact" }
    ];

    // Current page path (pass this from your layout/page)
    export let currentPath = "/";
</script>

<nav class="sidebar" aria-label="Sidebar Navigation">
    {#each items as item}
        <a
            href={item.href}
            class:active={currentPath === item.href}
        >
            {item.label}
        </a>
    {/each}
</nav>

<style>
  .sidebar {
    position: sticky;
    top: var(--gap-inner);
  }

  a {
    color: #232f3e;
    text-decoration: none;
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
    display: block;
    border-left: 3px solid transparent;
    transition: background-color 0.2s ease, border-color 0.2s ease;
  }

  a:hover,
  a.active {
    background-color: rgba(31, 111, 235, 0.08);
    border-left: 3px solid #1f6ffb;
    font-weight: bold;
  }
</style>
