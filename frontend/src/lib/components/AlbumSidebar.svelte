<!--
  AlbumSidebar
  Purpose: Thin adapter over Sidebar for Album views. Maps the Album's Sides and Snippets
    into Sidebar sections, with each Snippet as a NavLink to ?snippet=<id>.
  Used in: /learn/[id]
  Props:
    - sides (SideResponse[]): the Album's Sides, each with its Snippets
    - activeSnippetId (number | null): id of the currently-viewed Snippet for active highlighting
-->
<script lang="ts">
  import type { SideResponse } from '$lib/api/types';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import type { SidebarSection } from '$lib/components/Sidebar.svelte';

  export let sides: SideResponse[];
  export let activeSnippetId: number | null;

  $: sections = sides.map(
    (side, i): SidebarSection => ({
      title: side.title,
      sideLabel: `SIDE ${i + 1}`,
      links: side.snippets.map((s) => ({
        label: s.title,
        href: `?snippet=${s.id}`,
      })),
    })
  );

  $: activeHref = activeSnippetId !== null ? `?snippet=${activeSnippetId}` : '';
</script>

<Sidebar {sections} {activeHref} ariaLabel="Album sides and snippets" />
