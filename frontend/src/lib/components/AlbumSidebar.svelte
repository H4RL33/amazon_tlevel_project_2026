<!--
  AlbumSidebar
  Purpose: Adapted version of NavSidebar shown within an Album view. Displays the Album's Sides
    (chapters) vertically, each with its constituent Snippets listed underneath via SideHeader.
  Used in: Album view
  Props:
    - sides (Side[] — TODO: replace with real API type once the Side model exists. Shape for
      now: { id: number; title: string; snippets: ContentListResponse[] })
    - activeSnippetId (number | null): id of the Snippet currently being read, for highlighting
  Layout:
    For each side: a SideHeader, followed by its snippets as a vertical list of links.
    The link matching activeSnippetId is highlighted.
  Styling:
    Same visual language as NavSidebar (background #0a2540, width 240px).
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';
  import SideHeader from '$lib/components/SideHeader.svelte';

  interface Side {
    id: number;
    title: string;
    snippets: ContentListResponse[];
  }

  export let sides: Side[];
  export let activeSnippetId: number | null;
</script>

<!-- TODO: Render a SideHeader + snippet link list for each side. Highlight activeSnippetId. -->
