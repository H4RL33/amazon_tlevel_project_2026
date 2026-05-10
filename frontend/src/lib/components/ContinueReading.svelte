<!--
  ContinueReading
  Purpose: Bottom-left dashboard section showing in-progress content items.
  Used in: /dashboard — occupies the bottom-left of the content area.
  Props:
    - items (ProgressResponse[]): in-progress items from GET /progress (progress_pct < 100)
  Layout:
    Horizontal scroll row of compact cards. Each card shows:
      - content.title (truncated to 2 lines)
      - ProgressBar with item.progress_pct
      - content_type Badge
    If items is empty: show "Nothing in progress yet." in muted text.
  Behaviour:
    Clicking a card should navigate to the content item — leave as a TODO for juniors.
  Styling:
    Heading "Continue Reading" same style as "For You" in PersonalisedFeed.
    Cards: min-width 200px, max-width 250px, background #161b22, border-radius 6px,
    padding 0.75rem, box-shadow 0 1px 3px rgba(0,0,0,0.3).
    Container: display flex, gap 0.75rem, overflow-x auto, padding-bottom 0.5rem.
-->
<script lang="ts">
  import type { ProgressResponse } from '$lib/api/types';
  import Badge from '$lib/components/Badge.svelte';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let items: ProgressResponse[];
</script>

<!-- TODO: Implement horizontal scroll row of in-progress content cards. -->
