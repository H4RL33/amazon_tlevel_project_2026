<!--
  AlbumSidebar
  Purpose: Adapted version of NavSidebar shown within an Album view. Displays the Album's Sides
    (chapters) vertically, each with its constituent Snippets listed underneath via SideHeader.
  Used in: /learn/[id]
  Props:
    - sides (SideResponse[]): the Album's Sides, each with its Snippets
    - activeSnippetId (number | null): id of the Snippet currently being read, for highlighting.
      Always null for now -- there's no Snippet detail page yet, so nothing can be "active."
      Kept as a prop so a future chapter can wire it up without changing this component's
      interface.
  Layout:
    For each side: a SideHeader, followed by its snippets as a vertical list. Snippets render
    as plain text (not links) for now, since there's no Snippet detail page to navigate to yet.
  Styling:
    Same visual language as NavSidebar (background #0a2540, width 240px).
-->
<script lang="ts">
  import type { SideResponse } from '$lib/api/types';
  import SideHeader from '$lib/components/SideHeader.svelte';

  export let sides: SideResponse[];
  export let activeSnippetId: number | null;
</script>

<nav class="album-sidebar" aria-label="Album sides and snippets">
  {#each sides as side, index}
    <SideHeader title={side.title} index={index + 1} />
    <ul>
      {#each side.snippets as snippet}
        <li
          class:active={snippet.id === activeSnippetId}
          aria-current={snippet.id === activeSnippetId ? 'true' : undefined}
        >
          {snippet.title}
        </li>
      {/each}
    </ul>
  {/each}
</nav>

<style>
  .album-sidebar {
    background: #0a2540;
    height: 100%;
    width: 240px;
    padding: 1rem 0.75rem;
    box-sizing: border-box;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li {
    color: #c9d1d9;
    font-size: 0.875rem;
    padding: 0.4rem 0;
  }

  li.active {
    font-weight: bold;
    color: #ffffff;
  }
</style>
