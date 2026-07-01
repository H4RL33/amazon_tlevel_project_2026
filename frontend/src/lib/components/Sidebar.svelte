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

<div class="sidebar-sticky">
  <PageCard as="aside" {width} padding="1.5rem 1rem" overflowY="auto">
    <nav class="sidebar-nav" aria-label={ariaLabel}>
      {#each sections as section}
        {#if section.title}
          <SideHeader title={section.title} label={section.sideLabel ?? ''} />
        {/if}
        <ul>
          {#each section.links as link}
            <li>
              <NavLink
                href={link.href}
                label={link.label}
                active={link.href === activeHref}
                muted
              />
            </li>
          {/each}
        </ul>
      {/each}
    </nav>
  </PageCard>
</div>

<style>
  /* Keeps the sidebar in view as the page's single scroll container
     (.content in +layout.svelte) scrolls the main content beside it.
     A wrapper div (rather than reaching into PageCard's own .page-card
     class) keeps PageCard's encapsulation intact — this element owns the
     sticky/max-height behaviour, PageCard just renders the floating card
     inside it.

     top: 16px matches .content's own padding-top (see +layout.svelte), so
     the sidebar sticks exactly where it already naturally sits at rest —
     no visual jump when it starts sticking.

     max-height caps this box to whatever of the viewport .content actually
     has left to show, so a sidebar taller than that (e.g. AlbumSidebar with
     many Sides, or a long topic list) scrolls internally via PageCard's own
     overflow-y: auto instead of spilling past the bottom of the viewport
     where it would be unreachable (sticky elements don't shrink themselves
     to fit — they just stop moving). Derived from the shell layout in
     +layout.svelte: 100dvh, minus the shell's top+bottom outer padding
     (2 x --gap-outer), minus the gap between Navbar and .content
     (--gap-inner), minus Navbar's fixed content height (48px, from
     Navbar.svelte's .nav-inner), minus .content's own top+bottom padding
     (16px + 48px, the latter being .content's shadow-clip buffer — see
     +layout.svelte) since the sticky box lives inside that padding.

     Caller requirement: .content (+layout.svelte) is `display: flex;
     flex-direction: column`, so whatever row wrapper places this component
     next to the main content (e.g. .settings-page, .album-page) is itself a
     flex item of a scrolling flex container. That row wrapper MUST set
     `flex-shrink: 0` — left at flex's default of 1, Chromium's sticky
     containing-block computation breaks and this element stops sticking
     entirely (scrolls 1:1 with .content instead), even though nothing here
     changes. Confirmed via Playwright; see .home-auth in the root
     +page.svelte for the reference fix. */
  .sidebar-sticky {
    position: sticky;
    top: 16px;
    max-height: calc(100dvh - (2 * var(--gap-outer)) - var(--gap-inner) - 48px - 16px - 48px);
    display: flex;
    flex-direction: column;
  }

  /* Lets the PageCard shrink to sidebar-sticky's max-height (rather than
     overflowing it) so its own overflow-y: auto can take over scrolling. */
  .sidebar-sticky :global(.page-card) {
    flex: 1 1 auto;
    min-height: 0;
  }

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
</style>
