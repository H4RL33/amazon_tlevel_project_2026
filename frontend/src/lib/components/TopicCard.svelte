<!--
  TopicCard
  Purpose: Single topic area card with name, description excerpt, and accent colour.
  Used in: TopicGrid
  Props:
    - topic (TopicResponse): the topic to display
    - selected (boolean): when true, show a blue ring (box-shadow: 0 0 0 2px #1f6feb)
    - selectable (boolean): when true, render as a button; when false, render as <a>
  Styling:
    Card base + 4px left border in topic.accent_colour.
    Hover: lift with box-shadow 0 4px 12px rgba(0,0,0,0.4), translateY(-2px).
    Selected ring: box-shadow 0 0 0 2px #1f6feb.
    When selectable: cursor pointer, no underline.
    Topic name: font-size 1rem, font-weight 600, color #c9d1d9.
    Description: first 80 chars of topic.description (strip Markdown), color #8b949e, font-size 0.8rem.
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';

  export let topic: TopicResponse;
  export let selected = false;
  export let selectable = false;
</script>

<!-- TODO: Render card. When selectable=false, wrap in <a href="/topics/{topic.slug}">. -->
<!-- When selectable=true, dispatch 'click' event (parent TopicGrid handles selection logic). -->
