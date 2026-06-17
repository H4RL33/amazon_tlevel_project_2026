<!--
  AppShell
  Purpose: Root layout wrapper for all authenticated pages.
  Used in: src/routes/(app)/+layout.svelte — wraps every protected page.
  Props: none — uses <slot /> for page content
  Layout:
    CSS grid with two columns: sidebar (240px fixed) + main content (1fr).
    Full viewport height (height: 100vh). No overflow on the shell itself —
    the content column scrolls independently.
  Styling:
    background #0d1117 (page background)
    The sidebar column contains <Sidebar />; the content column contains <slot />.
-->
<script lang="ts">
  import Sidebar from '$lib/components/Sidebar.svelte';
  import { currentUser } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';
</script>

<!-- TODO: Implement two-column grid layout with Sidebar and <slot /> -->
