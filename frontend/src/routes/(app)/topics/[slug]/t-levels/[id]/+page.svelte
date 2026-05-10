<!--
  T-Level Detail — /topics/[slug]/t-levels/[id]
  Protected.
  Purpose: Show full T-level detail: entry requirements, how to apply, and related content.
  Data fetching (on mount):
    - GET /topics/{slug}/t-levels/{id} → tLevel (TLevelResponse)
    - GET /content?t_level_id={id} → tLevelContent (ContentListResponse[])
    - For each tLevelContent item: GET /content/{id} when user clicks to expand (lazy)
  Layout:
    - Breadcrumb: [{ label: 'Topics', href: '/dashboard' }, { label: topicName, href: '/topics/{slug}' }, { label: tLevel.name, href: '' }]
    - Main content (single column, max-width 800px):
        h1: tLevel.name
        Section "Entry Requirements": render tLevel.entry_requirements as Markdown
        Section "How to Apply": render tLevel.how_to_apply as Markdown
        Section "Related Content": list of ContentBlock components for tLevelContent
    - Left: TLevelList (same topic's T-levels, activeId = current id) for in-page navigation
  Styling: same two-column pattern as topic page (TLevelList left, content right).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { getTLevel, getTopic } from '$lib/api/topics';
  import { listContent } from '$lib/api/content';
  import type { ContentListResponse, TLevelResponse, TopicDetailResponse } from '$lib/api/types';
  import TLevelList from '$lib/components/TLevelList.svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';

  // Scaffold: will be assigned in onMount once API is wired up.
   
  let tLevel = null as TLevelResponse | null;
   
  let topic = null as TopicDetailResponse | null;
  let tLevelContent: ContentListResponse[] = [];

  onMount(async () => {
    const { slug, id } = $page.params;
    // TODO: fetch tLevel, topic, and tLevelContent in parallel
    void slug;
    void id;
  });

  $: pageTitle = tLevel ? tLevel.name : 'T-Level';
</script>

<svelte:head><title>{pageTitle} — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with Breadcrumb, TLevelList (active), and T-level detail. -->
