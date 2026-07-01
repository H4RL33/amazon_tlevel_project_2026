<!--
  Card
  Purpose: Surface container for grouped content.
  Used in: topic cards, T-level list items, content blocks.
  Props:
    - title (string | undefined): optional heading rendered above the default slot
  Slots:
    - default: main card body content
    - actions: optional footer row for action buttons (right-aligned)
  Styling:
    background #161b22, border-radius 8px, padding 1.5rem,
    box-shadow 0 1px 4px rgba(0,0,0,0.3), border 1px solid #21262d
-->
<script lang="ts">
  export let title: string | undefined = undefined;
</script>

<!-- TODO: Implement card template with optional title, default slot, and actions slot -->
