<!--
  TLevelList
  Purpose: Left-column list of T-levels for a topic page.
  Used in: /topics/[slug]/+page.svelte — occupies the left column.
  Props:
    - tLevels (TLevelResponse[]): all T-levels for the current topic
    - activeId (number | null): id of the currently active T-level (if viewing detail)
  Behaviour:
    Each item links to /topics/[slug]/t-levels/[id].
    The item matching activeId is highlighted.
    If tLevels is empty: show "No T-levels available for this topic yet."
  Styling:
    Vertical list, no bullets, gap 2px between items.
    Container: min-width 220px, max-width 260px.
-->
<script lang="ts">
  import type { TLevelResponse } from '$lib/api/types';
  import TLevelListItem from '$lib/components/TLevelListItem.svelte';

  export let tLevels: TLevelResponse[];
  export let activeId: number | null;
</script>

<!-- TODO: Render a TLevelListItem for each tLevel. Pass active={tLevel.id === activeId}. -->
