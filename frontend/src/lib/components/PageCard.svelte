<!--
  PageCard
  Purpose: Shared "floating panel" surface used by every piece of page chrome (Navbar,
    Footer, sidebars, page content) to get the same white background, square corners,
    and omnidirectional drop shadow over the animated gradient backdrop.
  Used in: Navbar, Footer, AlbumSidebar, NavSidebar, CTASidebar, and every routed page's
    content area.
  Props:
    - as (string): root element tag to render, e.g. 'main' | 'nav' | 'footer' | 'aside' |
      'div'. Defaults to 'div'. Lets each consumer keep correct page semantics (e.g. a
      page's content area renders as <main>, a sidebar as <aside>) while sharing one
      visual implementation.
    - padding (string): CSS padding shorthand for the card's own internal padding,
      between its border and its slotted content. Defaults to '2rem'. Distinct from the
      --gap-inner/--gap-outer spacing between cards, which callers control themselves.
    - width (string): CSS width. Defaults to 'auto' (fills whatever flex/grid track the
      caller places it in) — used by sidebars/CTASidebar to set a fixed width.
  Styling:
    background #ffffff, border-radius 0 (square corners), box-shadow
    0 10px 18px -4px rgba(35, 47, 62, 0.35) (the validated "soft directional blur" shadow).
    overflow-y: auto so that when a caller constrains this card's height (e.g. via
    flex stretch in a fixed-height row), excess content scrolls inside the card
    instead of growing it — a no-op when height is left at its natural auto size.
-->
<script lang="ts">
  export let as: string = 'div';
  export let padding: string = '2rem';
  export let width: string = 'auto';
</script>

<svelte:element this={as} class="page-card" style="padding: {padding}; width: {width};">
  <slot />
</svelte:element>

<style>
  .page-card {
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    box-sizing: border-box;
    overflow-y: auto;
  }
</style>
