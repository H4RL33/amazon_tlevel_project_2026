<!--
  ContentBlock
  Purpose: Renders a single Content item — Markdown article or media player.
  Used in: /topics/[slug]/+page.svelte (topic-level content),
           /topics/[slug]/t-levels/[id]/+page.svelte (T-level content).
  Props:
    - content (ContentDetailResponse): the full content item including body and media_url
  Behaviour:
    - content_type === 'article': render content.body as Markdown HTML using `marked`.
      Import: import { marked } from 'marked'
      Render: {@html marked(content.body ?? '')}
      Wrap in a div with class "prose" for typography styles.
    - content_type === 'audio': render <AudioPlayer contentId={content.id} src={content.media_url ?? ''} />
    - content_type === 'video': render <VideoPlayer contentId={content.id} src={content.media_url ?? ''} />
  Styling:
    Card wrapper (use Card component), title as h3 (font-size 1rem, font-weight 600).
    Prose styles (apply to .prose): line-height 1.7, color #c9d1d9, font-size 0.95rem,
    h1-h3 color #fff, a color #1f6feb, code background #21262d, border-radius 3px, padding 0.1rem 0.3rem.
-->
<script lang="ts">
  import { marked } from 'marked';
  import type { ContentDetailResponse } from '$lib/api/types';
  import AudioPlayer from '$lib/components/AudioPlayer.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Card from '$lib/components/Card.svelte';

  export let content: ContentDetailResponse;
</script>

<!-- TODO: Implement content rendering — switch on content.content_type. -->
