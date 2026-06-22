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
<script lang="ts">
  export let targetId: number;
  export let targetType: 'post' | 'snippet';
  export let liked: boolean;
  export let count: number;
</script>

<!-- TODO: Implement optimistic toggle + API call described above, with rollback on failure. -->
