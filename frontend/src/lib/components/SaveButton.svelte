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
<script lang="ts">
  export let targetId: number;
  export let targetType: 'post' | 'snippet';
  export let saved: boolean;
</script>

<!-- TODO: Implement optimistic toggle + API call described above, with rollback on failure. -->
