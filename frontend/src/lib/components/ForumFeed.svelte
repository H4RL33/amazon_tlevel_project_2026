<!--
  ForumFeed
  Purpose: Scrollable container of PostCards forming the main Forum feed view. The Forum is
    age-gated: posts are visible from age 14 (Learning tier), but only Career tier (16+) users
    see write actions — this component renders whatever `posts` it's given and assumes the
    caller has already applied age-tier filtering server-side.
  Used in: /forum
  Props:
    - posts (Post[] — same placeholder shape as PostCard's `post` prop, until the Post model
      exists on the backend)
    - ageTier ('exploring' | 'learning' | 'career'): the current user's age tier, used only to
      decide whether to render PostComposer above the feed (career only) — NOT used to filter
      `posts`, which must already be filtered server-side per CLAUDE.md's age-tier rules.
  Behaviour:
    If posts is empty, show an empty state: "No posts yet."
  Styling:
    Vertical scroll, gap 1rem between PostCards.
-->

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">
  // Shared API type representing a forum user.
  import type { UserResponse } from '$lib/api/types';

  // Component displayed above the feed that allows eligible users to create a post.
  import PostComposer from '$lib/components/PostComposer.svelte';

  // Component responsible for rendering an individual forum post.
  import PostCard from '$lib/components/PostCard.svelte';

  /**
   * Temporary placeholder Post model.
   * This should be replaced with the shared backend Post type
   * once it becomes available.
   */
  interface Post {
    id: number;
    author: UserResponse;
    body: string;
    mediaUrl: string | null;
    mediaType: 'image' | 'video' | null;
    likeCount: number;
    liked: boolean;
    saved: boolean;
    createdAt: string;
  }

  /**
   * Posts to render in the feed.
   * Filtering based on age tier has already been performed by the server.
   */
  export let posts: Post[];

  /**
   * Current user's age tier.
   * Used only to determine whether the PostComposer is shown.
   */
  export let ageTier: 'exploring' | 'learning' | 'career';
</script>

<!-- Scrollable container for the forum feed. -->
<div class="forum-feed">

  <!--
    Only Career-tier users (16+) are permitted to create new posts.
    Users in lower age tiers can still browse the posts supplied
    by the parent component.
  -->
  {#if ageTier === 'career'}
    <PostComposer />
  {/if}

  <!-- Render the feed if posts are available. -->
  {#if posts.length > 0}

    <!--
      Render a PostCard for each post.
      The post's unique ID is used as the key so Svelte can efficiently
      update the list when posts are added, removed, or reordered.
    -->
    {#each posts as post (post.id)}
      <PostCard {post} />
    {/each}

  {:else}

    <!-- Displayed when there are no posts to show. -->
    <p class="empty-state">No posts yet.</p>

  {/if}

</div>

<style>
  /* Main forum feed layout. */
  .forum-feed {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    /* Allow the feed to scroll when its content exceeds the available height. */
    overflow-y: auto;
  }

  /* Styling for the empty-state message. */
  .empty-state {
    padding: 2rem;
    text-align: center;
    color: #8b949e;
  }
</style>


<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->

<!-- TODO: Render PostComposer when ageTier === 'career', then a PostCard per post, or the empty state. -->
