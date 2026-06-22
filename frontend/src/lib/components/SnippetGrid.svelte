<!--
  SnippetGrid
  Purpose: Grid/list of SnippetCards for public browsing or search results of standalone
    Snippets (not scoped to one Album).
  Used in: Snippet discovery/search page
  Props:
    - snippets (ContentListResponse[]): the Snippets to display
  Behaviour:
    If snippets is empty, show an empty state: "No Snippets found."
  Styling:
    CSS grid, responsive square-ish columns (e.g. repeat(auto-fill, minmax(160px, 1fr))),
    gap 1rem.
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';

  export let snippets: ContentListResponse[];
</script>

<!-- TODO: Render a SnippetCard per snippet. Show the empty state when snippets.length === 0. -->
