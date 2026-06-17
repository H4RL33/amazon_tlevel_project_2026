<!--
  TopicGrid
  Purpose: Displays all 5 topic area cards in a 2×3 grid (5 topics + 1 "Explore All" card).
  Used in: /dashboard (read-only), /onboarding (selectable multi-select).
  Props:
    - topics (TopicResponse[]): all 5 topics from allTopics store
    - selectable (boolean): when true, cards toggle selected state instead of navigating.
      Used on the onboarding page for topic interest selection.
    - selected (number[]): topic ids currently selected (only used when selectable=true)
  Events:
    - selectionChange: dispatched when selectable=true and user toggles a card.
      Payload: { ids: number[] } — full updated list of selected topic ids.
  Styling:
    CSS grid, 2 columns, gap 1rem.
    When selectable=true, clicking a TopicCard toggles it; no navigation.
    When selectable=false, TopicCard is a link to /topics/[slug].
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { TopicResponse } from '$lib/api/types';
  import TopicCard from '$lib/components/TopicCard.svelte';

  export let topics: TopicResponse[];
  export let selectable = false;
  export let selected: number[] = [];

  const dispatch = createEventDispatcher<{ selectionChange: { ids: number[] } }>();
</script>

<!-- TODO: Render a TopicCard for each topic. Handle selectionChange dispatch when selectable. -->
