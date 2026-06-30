<!--
  NavSidebar
  Purpose: Thin adapter over Sidebar for scroll-navigation sidebars (e.g. /learn, /t-levels/[slug]).
    Accepts a flat list of anchor links and an activeHref updated by IntersectionObserver.
  Used in: /learn, /t-levels/[slug]
  Props:
    - links ({ label: string; href: string }[]): ordered list of anchor/page links
    - activeHref (string): href of the currently-visible section
-->
<script lang="ts">
  import Sidebar from '$lib/components/Sidebar.svelte';
  import type { SidebarSection } from '$lib/components/Sidebar.svelte';

  export let links: { label: string; href: string }[] = [];
  export let activeHref: string = '';

  $: sections = [{ links }] satisfies SidebarSection[];
</script>

<Sidebar {sections} {activeHref} ariaLabel="Section navigation" />
