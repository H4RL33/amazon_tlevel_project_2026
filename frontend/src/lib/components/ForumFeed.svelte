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
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';
  import PostComposer from '$lib/components/PostComposer.svelte';

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

  export let posts: Post[];
  export let ageTier: 'exploring' | 'learning' | 'career';
</script>

<!-- TODO: Render PostComposer when ageTier === 'career', then a PostCard per post, or the empty state. -->
