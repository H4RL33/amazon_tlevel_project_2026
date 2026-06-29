<!--
  NavSidebar
  Purpose: Section-navigation sidebar used on /learn and /t-levels/[slug]. Renders a
    vertical list of anchor links that scroll to named sections on the same page. The
    active link is highlighted based on the activeHref prop, which the parent page
    updates via IntersectionObserver as the user scrolls.
  Used in: /learn, /t-levels/[slug]
  Props:
    - links ({ label: string; href: string }[]): ordered list of anchor links
    - activeHref (string): href of the currently-visible section, e.g. "#digital"
-->
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';

  export let links: { label: string; href: string }[];
  export let activeHref: string = '';
</script>

<PageCard as="aside" width="288px" padding="1.5rem 1rem">
  <nav class="sidebar">
    {#each links as link}
      <a href={link.href} class:active={link.href === activeHref}>
        {link.label}
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
    padding-left: 0.5rem;
  }
</style>
