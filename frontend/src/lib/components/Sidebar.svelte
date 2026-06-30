<!--
  Sidebar
  Purpose: Universal declarative sidebar used across all pages. Renders sections of NavLinks
    inside a floating PageCard aside. Replaces NavSidebar and is the base for AlbumSidebar.
  Used in: AlbumSidebar, NavSidebar, /settings, and any page needing a left-hand nav panel.
  Props:
    - sections (SidebarSection[]): ordered list of sections, each with optional title/sideLabel
      and a list of links. Links may be page URLs ("/settings"), anchors ("#digital"), or
      query params ("?snippet=3").
    - activeHref (string): href matched === against link.href to determine the active link.
    - width (string): CSS width of the PageCard. Defaults to '288px'.
    - ariaLabel (string): accessible label for the <nav> element.
-->
<script lang="ts" context="module">
  export interface SidebarLink {
    label: string;
    href: string;
  }

  export interface SidebarSection {
    title?: string;
    sideLabel?: string;
    links: SidebarLink[];
  }
</script>

<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import SideHeader from '$lib/components/SideHeader.svelte';

  export let sections: SidebarSection[] = [];
  export let activeHref: string = '';
  export let width: string = '288px';
  export let ariaLabel: string = 'Page navigation';
</script>

<PageCard as="aside" {width} padding="1.5rem 1rem" overflowY="auto">
  <nav class="sidebar-nav" aria-label={ariaLabel}>
    {#each sections as section}
      {#if section.title}
        <SideHeader title={section.title} label={section.sideLabel ?? ''} />
      {/if}
      <ul>
        {#each section.links as link}
          <li class:active={link.href === activeHref}>
            <NavLink href={link.href} label={link.label} />
          </li>
        {/each}
      </ul>
    {/each}
  </nav>
</PageCard>

<style>
  .sidebar-nav {
    display: flex;
    flex-direction: column;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li {
    font-size: 0.875rem;
    padding: 0.4rem 0;
  }

  li :global(a) {
    color: #5a6472 !important;
    font-family: 'Ubuntu', sans-serif;
  }

  li.active :global(a) {
    font-weight: 700;
    color: #232f3e !important;
  }
</style>
