<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { ContentListResponse } from '$lib/api/types';
  import SnippetCard from './SnippetCard.svelte';

  export let Hst: Hst;

  const articleSnippet: ContentListResponse = {
    id: 1,
    title: 'What is Virtualisation?',
    content_type: 'article',
    topic_id: 1,
    t_level_id: null,
    tags: [],
    created_at: new Date().toISOString(),
  };

  const videoSnippet: ContentListResponse = {
    id: 2,
    title: 'Intro to VLANs',
    content_type: 'video',
    topic_id: 1,
    t_level_id: null,
    tags: [],
    created_at: new Date().toISOString(),
  };
</script>

<Hst.Story title="SnippetCard">
  <Hst.Variant title="Article">
    <SnippetCard content={articleSnippet} />
  </Hst.Variant>

  <Hst.Variant title="Video, with XP">
    <SnippetCard content={videoSnippet} xp={50} />
  </Hst.Variant>

  <Hst.Variant title="Saveable, unsaved">
    <SnippetCard content={articleSnippet} onSaveToggle={() => {}} saved={false} />
  </Hst.Variant>

  <Hst.Variant title="Saveable, saved">
    <SnippetCard content={articleSnippet} onSaveToggle={() => {}} saved={true} />
  </Hst.Variant>
</Hst.Story>
