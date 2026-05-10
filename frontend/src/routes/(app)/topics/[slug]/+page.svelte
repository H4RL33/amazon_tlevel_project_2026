<!--
  Topic Page — /topics/[slug]
  Protected.
  Purpose: Show topic description (right), T-level list (left), and topic content (below).
  Data fetching (on mount):
    - GET /topics/{slug} → topic (TopicDetailResponse — includes t_levels list)
    - GET /content?topic={slug} → topicContent (ContentListResponse[])
    - GET /content/{id} for each item clicked (lazy — fetch detail on T-level selection)
  Layout:
    - Breadcrumb at top: [{ label: 'Topics', href: '/dashboard' }, { label: topic.name, href: '' }]
    - Two-column below breadcrumb:
        Left (260px): TLevelList with topic.t_levels
        Right (flex: 1):
          - Topic description (render topic.description as Markdown using marked)
          - Section heading "Related Content"
          - ContentBlock for each item in topicContent
  Styling: padding 1.5rem, gap 1.5rem between columns.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { getTopic } from '$lib/api/topics';
  import { listContent } from '$lib/api/content';
  import type { ContentListResponse, TopicDetailResponse } from '$lib/api/types';
  import TLevelList from '$lib/components/TLevelList.svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';

  // Scaffold: will be assigned in onMount once API is wired up.

  let topic = null as TopicDetailResponse | null;
  let topicContent: ContentListResponse[] = [];

  onMount(async () => {
    const slug = $page.params.slug;
    // TODO: [topic, topicContent] = await Promise.all([getTopic(slug), listContent({ topic: slug })]);
    void slug;
  });

  $: pageTitle = topic ? topic.name : 'Topic';
</script>

<svelte:head><title>{pageTitle} — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with Breadcrumb, TLevelList, description, and content blocks. -->
