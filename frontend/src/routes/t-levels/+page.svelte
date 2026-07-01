<script lang="ts">
  import { onMount } from 'svelte';
  import { listTopics } from '$lib/api/topics';
  import type { TopicResponse } from '$lib/api/types';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  let topics: TopicResponse[] = [];
  let loading = true;
  let error: string | null = null;

  const TOPIC_ICONS: Record<string, string> = {
    'digital-production-design-development': 'code',
    'digital-business-services': 'briefcase',
    'digital-infrastructure': 'cloud',
    'design-surveying-planning': 'compass',
    health: 'heart',
  };

  onMount(async () => {
    try {
      topics = await listTopics();
    } catch {
      error = 'Could not load T-Levels right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<PageCard as="main" padding="1.5rem">
  {#if loading}
    <p class="status">Loading...</p>
  {:else if error}
    <p class="status">{error}</p>
  {:else}
    <div class="topic-grid">
      {#each topics as topic}
        <AlbumCard
          label={topic.name}
          href="/t-levels/{topic.slug}"
          icon={TOPIC_ICONS[topic.slug]}
        />
      {/each}
    </div>
  {/if}
</PageCard>

<style>
  .topic-grid {
    display: grid;
    grid-template-columns: repeat(2, 190px);
    gap: 1.5rem;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
