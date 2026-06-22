<!--
  SnippetCard
  Purpose: Square card used to open a Snippet — a single short-form piece of content
    (article / audio / video). Publicly accessible without an account.
  Used in: CTASidebar, SnippetGrid, LibraryShelf
  Props:
    - content (ContentListResponse): the Snippet to display
    - xp (number | undefined): XP available for reading this Snippet — shown via XPBadge if set
  Layout:
    Centered icon (derive from content.content_type — article/audio/video), title below it.
    Optional XPBadge in the top-right corner if xp is provided.
  Styling:
    Square aspect ratio, Card base, centered flex column, icon ~32px,
    title font-size 0.85rem, font-weight 600, text-align center.
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';
  import XPBadge from '$lib/components/XPBadge.svelte';

  export let content: ContentListResponse;
  export let xp: number | undefined = undefined;
</script>

<!-- TODO: Implement centered icon + title layout. Render XPBadge in the corner when xp is set. -->
