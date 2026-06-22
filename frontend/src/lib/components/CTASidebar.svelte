<!--
  CTASidebar
  Purpose: Wide left sidebar on the dashboard with a personalised, time-of-day-aware welcome
    message, two enrolled AlbumCards, three recommended SnippetCards, and an AgentChat teaser.
  Used in: /dashboard
  Props:
    - user (UserResponse): used to render "Good morning/afternoon/evening, {first_name}"
    - albums (Album[] — TODO: replace with real API type once the Album model exists; for now
      whatever shape AlbumCard expects, max 2 items shown)
    - snippets (ContentListResponse[]): recommended Snippets, max 3 items shown
  Layout (top to bottom):
    1. Welcome message (derive greeting from local time-of-day)
    2. Two AlbumCards, stacked vertically
    3. Three SnippetCards, laid out horizontally
    4. AgentChat teaser at the bottom
  Styling:
    Wider than NavSidebar (~320px), background matches dashboard surface, gap 1.5rem between
    sections.
-->
<script lang="ts">
  import type { ContentListResponse, UserResponse } from '$lib/api/types';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';
  import AgentChat from '$lib/components/AgentChat.svelte';

  interface Album {
    id: number;
    title: string;
  }

  export let user: UserResponse;
  export let albums: Album[];
  export let snippets: ContentListResponse[];
</script>

<!-- TODO: Implement greeting (time-of-day), then render albums.slice(0, 2) as AlbumCards, -->
<!-- snippets.slice(0, 3) as SnippetCards, then an AgentChat at the bottom. -->
