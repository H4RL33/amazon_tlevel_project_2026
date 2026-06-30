<!--
  Badge
  Purpose: Small pill label for content type or topic name.
  Used in: SnippetCard (content type), PostCard (category labels) — TODO: wire in as those stubs are implemented.
  Props:
    - label (string): text displayed inside the badge
    - colour (string | undefined): hex colour used for background at 20% opacity and text.
      If undefined, use #1f6feb (AWS blue).
  Styling:
    display inline-block, border-radius 999px, padding 0.2rem 0.6rem,
    font-size 0.7rem, font-weight 600, letter-spacing 0.03em,
    background = colour at 20% opacity, color = colour
-->
<script lang="ts">
  export let label: string;
  export let colour: string | undefined = undefined;
</script>

<!-- TODO: Implement badge template. Use inline style for dynamic colour. -->
