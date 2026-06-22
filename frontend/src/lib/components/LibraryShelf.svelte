<!--
  LibraryShelf
  Purpose: Grid/list of the user's saved Snippets, shown in The Library.
  Used in: /library
  Props:
    - snippets (ContentListResponse[]): the user's saved Snippets (TODO: define the
      `/library/snippets` endpoint that returns these)
  Behaviour:
    If snippets is empty, show an empty state: "Nothing saved yet — save a Snippet to read it
    later."
  Styling:
    Same grid treatment as SnippetGrid — reuse it internally rather than duplicating layout.
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';
  import SnippetGrid from '$lib/components/SnippetGrid.svelte';

  export let snippets: ContentListResponse[];
</script>

<!-- TODO: Render SnippetGrid with snippets, or the empty state when snippets.length === 0. -->
