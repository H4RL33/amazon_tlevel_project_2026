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

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">
  // Response type returned from the API for snippet listings.
  import type { ContentListResponse } from '$lib/api/types';

  // Component used to display an individual snippet.
  import SnippetCard from '$lib/components/SnippetCard.svelte';

  /**
   * Collection of snippets to display.
   */
  export let snippets: ContentListResponse[];
</script>

<!-- Grid container for the snippet cards. -->
<div class="snippet-grid">

  <!-- Render the grid when snippets are available. -->
  {#if snippets.length > 0}

    <!--
      Render a SnippetCard for each snippet.
      A unique ID is used as the key so Svelte can efficiently
      update the grid when the data changes.
    -->
    {#each snippets as snippet (snippet.id)}
      <SnippetCard {snippet} />
    {/each}

  {:else}

    <!-- Displayed when no snippets are available. -->
    <p class="empty-state">No Snippets found.</p>

  {/if}

</div>

<style>
  /* Responsive grid layout for snippet cards. */
  .snippet-grid {
    display: grid;

    /* Create as many columns as will fit while maintaining
       a minimum card width of 160px. */
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));

    /* Space between cards. */
    gap: 1rem;
  }

  /* Styling for the empty-state message. */
  .empty-state {
    grid-column: 1 / -1;
    padding: 2rem;
    text-align: center;
    color: #8b949e;
  }
</style>

<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->

<!-- TODO: Render a SnippetCard per snippet. Show the empty state when snippets.length === 0. -->
