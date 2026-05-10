<!--
  Dashboard — /dashboard
  Protected.
  Purpose: Main authenticated home page.
  Layout (two-column content area, inside AppShell):
    Left column (flex: 1):
      - TopicGrid (top, read-only, shows user's chosen topics from $userTopics)
      - ContinueReading (bottom, items from $continueReading)
    Right column (width: 320px, fixed):
      - PersonalisedFeed
  Data fetching (on mount):
    - GET /feed → feedItems (local variable)
    - $continueReading and $allTopics already populated by (app)/+layout.svelte
  Styling:
    Content area: display flex, gap 1.5rem, padding 1.5rem.
    Left column scrolls independently. Right column is sticky (position sticky, top 0).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { getFeed } from '$lib/api/feed';
  import type { ContentListResponse } from '$lib/api/types';
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import PersonalisedFeed from '$lib/components/PersonalisedFeed.svelte';
  import ContinueReading from '$lib/components/ContinueReading.svelte';
  import { allTopics } from '$lib/stores/topics';
  import { continueReading } from '$lib/stores/progress';

  let feedItems: ContentListResponse[] = [];

  onMount(async () => {
    // TODO: feedItems = await getFeed();
  });
</script>

<svelte:head><title>Dashboard — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with TopicGrid, ContinueReading, PersonalisedFeed. -->
