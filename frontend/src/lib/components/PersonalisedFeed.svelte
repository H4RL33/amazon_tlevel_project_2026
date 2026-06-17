<!--
  PersonalisedFeed
  Purpose: Right-column container for the personalised content feed on the dashboard.
  Used in: /dashboard — occupies the right column of the content area.
  Props:
    - items (ContentListResponse[]): feed items from GET /feed
    - userProgress (ProgressResponse[]): current user progress, used to show progress_pct on FeedItems
  Behaviour:
    - If items is empty, show a friendly empty state:
      "Nothing in your feed yet — choose some topics to get started."
    - Each item renders as a FeedItem component.
    - Pass progress_pct to FeedItem if a matching ProgressResponse exists for item.id.
  Styling:
    Scrollable column (overflow-y: auto), gap 0.75rem between FeedItems.
    Heading "For You" in font-size 0.7rem, font-weight 700, letter-spacing 0.08em,
    color #8b949e, margin-bottom 0.75rem.
-->
<script lang="ts">
  import type { ContentListResponse, ProgressResponse } from '$lib/api/types';
  import FeedItem from '$lib/components/FeedItem.svelte';

  export let items: ContentListResponse[];
  export let userProgress: ProgressResponse[];
</script>

<!-- TODO: Implement feed column with "For You" heading, FeedItem list, and empty state. -->
