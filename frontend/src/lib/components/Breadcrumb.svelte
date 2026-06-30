<!--
  Breadcrumb
  Purpose: Shows page hierarchy on topic and T-level pages.
  Used in: /topics/[slug]/+page.svelte, /topics/[slug]/t-levels/[id]/+page.svelte
  Props:
    - crumbs (Array<{ label: string; href: string }>): ordered list of breadcrumb items.
      The last item is the current page (rendered as plain text, not a link).
  Example crumbs for a T-level page:
    [{ label: 'Topics', href: '/dashboard' }, { label: 'Digital', href: '/topics/digital' }, { label: 'T-Level Name', href: '' }]
  Styling:
    font-size 0.8rem, color #8b949e, separator ' / ' between items,
    last item color #c9d1d9 (non-linked, current page)
-->
<!--
  Breadcrumb
  Displays the user's current location within the site hierarchy.

  Props:
    - crumbs: Ordered list of breadcrumb items.
      The final item represents the current page and is displayed as plain text.
-->

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">
  // Breadcrumb items to display.
  // Each item contains:
  // - label: Text shown to the user.
  // - href: Link destination (ignored for the final item).
  export let crumbs: Array<{ label: string; href: string }>;
</script>

<nav aria-label="Breadcrumb">
  {#each crumbs as crumb, index}
    {#if index < crumbs.length - 1}
      <!--
        Render all breadcrumb items except the last as links.
      -->
      <a href={crumb.href}>{crumb.label}</a>

      <!-- Separator between breadcrumb items. -->
      <span class="separator"> / </span>
    {:else}
      <!--
        The final breadcrumb represents the current page.
        It is displayed as plain text instead of a link.
      -->
      <span class="current">{crumb.label}</span>
    {/if}
  {/each}
</nav>

<!-- TODO: Render crumbs separated by '/'. Make all items except the last into <a> links. -->
<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->

<style>
  /* Container for the breadcrumb navigation. */
  nav {
    font-size: 0.8rem;
    color: #8b949e;
  }

  /* Style for breadcrumb links. */
  a {
    color: #8b949e;
    text-decoration: none;
  }

  /* Underline links when hovered for accessibility. */
  a:hover {
    text-decoration: underline;
  }

  /* Separator between breadcrumb items. */
  .separator {
    color: #8b949e;
  }

  /* Current page styling. */
  .current {
    color: #c9d1d9;
  }
</style>
