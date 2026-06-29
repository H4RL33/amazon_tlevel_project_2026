<!--
  SaveButton
  Purpose: Reusable save control shared between PostCard and Snippets. Saving adds the item to
    the user's personal Library.
  Used in: PostCard, SnippetCard (or wherever Snippet-level saving is surfaced)
  Props:
    - targetId (number): id of the Post or Snippet being saved
    - targetType ('post' | 'snippet'): which API to call when toggling
    - saved (boolean): current save state for this user
  Behaviour:
    Clicking toggles `saved` optimistically, then calls the relevant save/unsave API
    (TODO: define `/posts/{id}/save` and Snippet-equivalent endpoints, and confirm how saved
    Posts vs saved Snippets are distinguished in LibraryShelf).
    On API failure, revert the optimistic update.
  Styling:
    Bookmark icon (filled when saved, outline when not), no count shown.
-->

<!-- Code may contain bugs -->
<!-- Changes ----------------------------------------->

<script lang="ts">
  // Component props supplied by the parent.
  // targetId: ID of the Post or Snippet to save.
  // targetType: Determines which API endpoint should be used.
  // saved: Current saved state received from the parent.
  export let targetId: number;
  export let targetType: 'post' | 'snippet';
  export let saved: boolean;

  // Local copy of the saved state.
  // This allows the button to update immediately (optimistic UI)
  // before the API request has completed.
  let is_saved = saved;

  // Keep the local state synchronised if the parent updates the
  // saved prop (for example, after refreshing data).
  $: is_saved = saved;

  // Prevents multiple requests being sent if the user repeatedly
  // clicks the button before the previous request finishes.
  let loading = false;

  /**
   * Sends a request to save the current item.
   * Uses different API endpoints depending on whether the item
   * is a Post or a Snippet.
   */
  async function save_item() {
    const endpoint =
      targetType === "post"
        ? `/api/posts/${targetId}/save`
        : `/api/snippets/${targetId}/save`;

    const response = await fetch(endpoint, {
      method: "POST"
    });

    // Throw an error so toggle_save() can roll back the UI.
    if (!response.ok) {
      throw new Error("Failed to save");
    }
  }

  /**
   * Sends a request to remove the current item from the user's
   * saved library.
   */
  async function un_save_item() {
    const endpoint =
      targetType === "post"
        ? `/api/posts/${targetId}/save`
        : `/api/snippets/${targetId}/save`;

    const response = await fetch(endpoint, {
      method: "DELETE"
    });

    // Throw an error so toggle_save() can restore the previous state.
    if (!response.ok) {
      throw new Error("Failed to unsave");
    }
  }

  /**
   * Toggles the saved state using an optimistic update.
   *
   * The UI changes immediately to improve responsiveness, then the
   * corresponding API request is sent. If the request fails, the
   * previous state is restored so the UI remains accurate.
   */
  async function toggle_save() {
    // Ignore additional clicks while a request is already running.
    if (loading) return;

    loading = true;

    // Store the previous value in case the request fails.
    const previous = is_saved;

    // Optimistically update the UI.
    is_saved = !previous;

    try {
      if (is_saved) {
        await save_item();
      } else {
        await un_save_item();
      }
    } catch (err) {
      // Restore the previous state if the API request fails.
      is_saved = previous;
      console.error(err);
    } finally {
      // Re-enable the button once the request has finished.
      loading = false;
    }
  }
</script>

<!--
  Clicking the button toggles the saved state.
  The button is disabled while an API request is in progress.
-->
<button on:click={toggle_save} disabled={loading}>
  {#if is_saved}
    🔖
  {:else}
    📑
  {/if}
</button>

<style>
  /* Remove the browser's default button styling. */
  button {
    background: none;
    border: none;
    padding: 0.5rem;
    cursor: pointer;
    color: #666;
    transition: color 0.2s ease, transform 0.15s ease;
  }

  /* Slight visual feedback when hovering over the button. */
  button:hover {
    color: #333;
    transform: scale(1.05);
  }

  /* Applied when the button has the 'saved' class. */
  button.saved {
    color: #f4b400;
  }

  /* Indicate that the button cannot currently be interacted with. */
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>

<!-- Changes ----------------------------------------->
<!-- Code may contain bugs -->