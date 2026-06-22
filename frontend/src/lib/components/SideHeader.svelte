<!--
  SideHeader
  Purpose: Divider/header inside AlbumSidebar marking the start of a Side (chapter) and grouping
    its constituent Snippets underneath it.
  Used in: AlbumSidebar
  Props:
    - title (string): the Side's title
    - index (number): the Side's position within the Album (e.g. for "Side 1", "Side 2" labels)
  Styling:
    Small uppercase label (e.g. "SIDE {index}"), font-size 0.7rem, letter-spacing 0.08em,
    color #8b949e, followed by the title in a slightly larger weight, with a divider line below.
-->
<script lang="ts">
  export let title: string;
  export let index: number;
</script>

<!-- TODO: Implement "SIDE {index}" label + title + divider line. -->
