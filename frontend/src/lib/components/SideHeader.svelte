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

<div class="side-header">
  <span class="label">SIDE {index}</span>
  <h4>{title}</h4>
  <hr />
</div>

<style>
  .side-header {
    margin: 1rem 0 0.5rem;
  }

  .label {
    display: block;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: #8b949e;
    text-transform: uppercase;
  }

  h4 {
    margin: 0.25rem 0 0.5rem;
    color: #c9d1d9;
    font-size: 0.95rem;
    font-weight: 600;
  }

  hr {
    border: none;
    border-top: 1px solid #21262d;
    margin: 0;
  }
</style>
