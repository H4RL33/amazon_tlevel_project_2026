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
<script lang="ts">
  export let crumbs: Array<{ label: string; href: string }>;
</script>

<!-- TODO: Render crumbs separated by '/'. Make all items except the last into <a> links. -->
