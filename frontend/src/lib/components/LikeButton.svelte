<!--
  LikeButton
  Purpose: Reusable like control with a count, shared between PostCard and Snippets. Acts as a
    lightweight KPI for content popularity.
  Used in: PostCard, SnippetCard (or wherever Snippet-level liking is surfaced)
  Props:
    - targetId (number): id of the Post or Snippet being liked
    - targetType ('post' | 'snippet'): which API to call when toggling
    - liked (boolean): current like state for this user
    - count (number): total like count to display
  Behaviour:
    Clicking toggles `liked` and increments/decrements `count` optimistically, then calls the
    relevant like/unlike API (TODO: define `/posts/{id}/like` and Snippet-equivalent endpoints).
    On API failure, revert the optimistic update.
  Styling:
    Icon (filled when liked, outline when not) + count, inline-flex, gap 0.3rem,
    color changes to an accent colour when liked.
-->

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">
  /**
   * Unique identifier of the Post or Snippet whose like state is being managed.
   */
  export let targetId: number;

  /**
   * Content type, used to determine which backend endpoint to call.
   */
  export let targetType: 'post' | 'snippet';

  /**
   * Indicates whether the current user has already liked the content.
   */
  export let liked: boolean;

  /**
   * Total number of likes currently recorded for the content.
   */
  export let count: number;

  /**
   * Prevents duplicate requests while a previous toggle is still pending.
   */
  let loading = false;

  /**
   * Optimistically toggles the like state.
   *
   * The UI is updated immediately to provide instant feedback while the
   * request is sent to the backend. If the request fails, the previous
   * state is restored so the UI remains consistent with the server.
   */
  async function toggleLike() {
    // Ignore additional clicks until the current request completes.
    if (loading) return;

    loading = true;

    // Store the previous values so they can be restored if necessary.
    const previousLiked = liked;
    const previousCount = count;

    // Optimistically update the UI.
    liked = !liked;
    count += liked ? 1 : -1;

    try {
      // Select the appropriate endpoint based on the content type.
      const endpoint =
        targetType === 'post'
          ? `/posts/${targetId}/like`
          : `/snippets/${targetId}/like`;

      // Like when the content is now liked; otherwise remove the like.
      const response = await fetch(endpoint, {
        method: liked ? 'POST' : 'DELETE'
      });

      // Treat any unsuccessful response as a failed request.
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to update like.', error);

      // Revert the optimistic update if the request failed.
      liked = previousLiked;
      count = previousCount;
    } finally {
      // Re-enable the button regardless of the outcome.
      loading = false;
    }
  }
</script>

<!--
  Reusable like button displaying the current like state and total count.
  The button is disabled while a request is in progress to prevent duplicate
  submissions.
-->
<button
  class="like-button"
  class:liked
  on:click={toggleLike}
  disabled={loading}
  aria-label={liked ? 'Unlike' : 'Like'}
>
  <!-- Display a filled heart when liked, otherwise an outlined heart. -->
  <span class="icon">
    {#if liked}
      ♥
    {:else}
      ♡
    {/if}
  </span>

  <!-- Current number of likes. -->
  <span class="count">{count}</span>
</button>

<style>
  /* Base styling shared by all LikeButton instances. */
  .like-button {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;

    border: none;
    background: none;
    padding: 0;

    color: #8b949e;
    cursor: pointer;
    font: inherit;

    transition: color 0.2s ease;
  }

  /* Highlight the button when the content has been liked. */
  .like-button.liked {
    color: #ff4d6d;
  }

  /* Visually indicate that the button is temporarily unavailable. */
  .like-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Heart icon. */
  .icon {
    font-size: 1rem;
    line-height: 1;
  }

  /* Like count text. */
  .count {
    font-size: 0.95rem;
  }
</style>

<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
 
<!-- TODO: Implement optimistic toggle + API call described above, with rollback on failure. -->
