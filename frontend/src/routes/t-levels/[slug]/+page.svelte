<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { ApiError } from '$lib/api/client';
  import { getTopic } from '$lib/api/topics';
  import type { TLevelWithAlbumsResponse, AlbumListResponse } from '$lib/api/types';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import NavSidebar from '$lib/components/NavSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  interface Section {
    id: string;
    heading: string;
    albums: AlbumListResponse[];
  }

  let sections: Section[] = [];
  let topicName = '';
  let loading = true;
  let error: string | null = null;
  let activeHref = '';
  let observer: IntersectionObserver | null = null;

  $: links = sections.map((s) => ({ label: s.heading, href: '#' + s.id }));

  onMount(() => {
    (async () => {
      const slug = $page.params.slug ?? '';

      try {
        const topic = await getTopic(slug);
        topicName = topic.name;

        sections = topic.t_levels
          .filter((t: TLevelWithAlbumsResponse) => t.albums.length > 0)
          .map((t: TLevelWithAlbumsResponse) => ({
            id: `t-level-${t.id}`,
            heading: t.name,
            albums: t.albums,
          }));
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 404) {
          goto('/t-levels');
          return;
        }
        error = 'Could not load this T-Level area. Please try again later.';
      } finally {
        loading = false;
      }

      if (sections.length === 0) return;

      await tick();

      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              activeHref = '#' + entry.target.id;
              break;
            }
          }
        },
        { rootMargin: '0px 0px -75% 0px', threshold: 0 },
      );

      const sectionEls = document.querySelectorAll('.sections section[id]');
      sectionEls.forEach((el) => observer?.observe(el));
    })();

    return () => observer?.disconnect();
  });
</script>

<div class="page-layout">
  {#if !loading && !error && sections.length > 0}
    <NavSidebar {links} {activeHref} />
  {/if}

  <div class="main">
    {#if loading}
      <PageCard as="main" padding="1.5rem">
        <p class="status">Loading...</p>
      </PageCard>
    {:else if error}
      <PageCard as="main" padding="1.5rem">
        <p class="status">{error}</p>
      </PageCard>
    {:else if sections.length === 0}
      <PageCard as="main" padding="1.5rem">
        <p class="status">No albums available in {topicName} yet.</p>
      </PageCard>
    {:else}
      <div class="sections">
        {#each sections as section}
          <section id={section.id}>
            <PageCard padding="0.875rem 1.25rem">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
            <PageCard as="div" padding="1.5rem">
              <AlbumGrid albums={section.albums} />
            </PageCard>
          </section>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .page-layout {
    display: flex;
    gap: var(--gap-inner);
    align-items: flex-start;
    min-height: 100%;
  }

  .main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .sections {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  section {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .section-heading {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
