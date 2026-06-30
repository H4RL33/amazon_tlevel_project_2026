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

  // The saved snippets passed in from the parent component.
  export let snippets: ContentListResponse[];
</script>

{#if snippets.length === 0}
  <!-- Show a simple message when there is nothing saved yet. -->
  <p class="empty-state">Nothing saved yet — save a Snippet to read it later.</p>
{:else}
  <!-- Reuse the shared snippet grid layout for the saved items. -->
  <SnippetGrid {snippets} />
{/if}

<style>
  .empty-state {
    margin: 0;
    color: #4b5563;
  }
</style>
