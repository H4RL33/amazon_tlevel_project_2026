<!--
  TLevelListItem
  Purpose: Single row in the T-level list for a topic page.
  Used in: TLevelList
  Props:
    - tLevel (TLevelResponse): the T-level to display
    - topicSlug (string): the topic's slug, used to build the href
    - active (boolean): when true, apply active styles
  Styling:
    padding 0.6rem 0.75rem, border-radius 4px, font-size 0.875rem,
    color #c9d1d9, cursor pointer, hover background #21262d.
    Active: font-weight 600, background rgba(31,111,235,0.1),
    border-left 3px solid #1f6feb, color #fff.
    Non-active: border-left 3px solid transparent.
    Include a right-facing chevron (›) at the right edge.
-->
<script lang="ts">
  import type { TLevelResponse } from '$lib/api/types';

  export let tLevel: TLevelResponse;
  export let topicSlug: string;
  export let active: boolean;
</script>

<!-- TODO: Render as <a href="/topics/{topicSlug}/t-levels/{tLevel.id}"> with active styles. -->
