<!--
  FeedItem
  Purpose: Single content item card in the personalised feed.
  Used in: PersonalisedFeed
  Props:
    - item (ContentListResponse): the content item to display
    - progressPct (number | null): user's progress on this item (null = not started)
  Layout:
    - Title: font-size 0.9rem, font-weight 600, color #c9d1d9
    - Below title: Badge for content_type + topic accent dot (3px circle in topic colour — look up accent from allTopics store)
    - If progressPct is not null: ProgressBar below the badges
  Behaviour:
    - Clicking navigates to /content/[item.id] (create this route if needed) or
      opens the content inline — leave as a TODO comment for juniors.
  Styling:
    background #161b22, border-radius 6px, padding 0.75rem 1rem,
    border-left 3px solid topic accent_colour, hover darkens background to #1c2128, cursor pointer.
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';
  import Badge from '$lib/components/Badge.svelte';
  import ProgressBar from '$lib/components/ProgressBar.svelte';
  import { allTopics } from '$lib/stores/topics';

  export let item: ContentListResponse;
  export let progressPct: number | null;
</script>

<!-- TODO: Implement feed item card. Derive topic accent_colour from $allTopics using item.topic_id. -->
