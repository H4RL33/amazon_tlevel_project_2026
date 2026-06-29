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

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->
<script lang="ts">
  // Text displayed inside the badge.
  export let label: string;

  // Main badge colour.
  // Defaults to AWS blue if no colour is provided.
  export let colour: string = '#1f6feb';

  // Reactive variable.
  // Whenever 'colour' changes, 'background' is recalculated.
  // Appending '33' to a 6-digit hex colour sets its opacity to ~20%.
  // Example: #1f6feb -> #1f6feb33
  $: background = `${colour}33`;
</script>

<!--
  Badge element.
  - Background uses the colour at 20% opacity.
  - Text uses the full solid colour.
-->
<span class="badge" style:background-color={background} style:color={colour}>
  {label}
</span>

<style>
  .badge {
    /* Allow the badge to size itself to its content. */
    display: inline-block;

    /* Fully rounded ends for the pill shape. */
    border-radius: 999px;

    /* Space around the text. */
    padding: 0.2rem 0.6rem;

    /* Small label styling. */
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
</style>

<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- TODO: Implement badge template. Use inline style for dynamic colour. -->