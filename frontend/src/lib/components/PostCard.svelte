<!--
  PostCard
  Purpose: Container for a single Forum post. Three-tier layout: poster info, post content,
    action buttons. There is no commenting feature — do not add one.
  Used in: ForumFeed
  Props:
    - post (Post — TODO: replace with a real API type once the Post model exists on the backend.
      Shape for now: { id: number; author: UserResponse; body: string; mediaUrl: string | null;
      mediaType: 'image' | 'video' | null; likeCount: number; liked: boolean; saved: boolean;
      createdAt: string })
  Layout (top to bottom):
    1. Poster row: avatar (circle), name, subtitle/role — see UserProfileHeader for style cues.
    2. Post body: text, and if present, an image or video (composite = text + media).
    3. Action row: LikeButton, a "repost" control (TODO: define repost behaviour), SaveButton.
  Styling:
    Card base (use Card component), gap 0.75rem between tiers.
-->

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">
  import Card from '$lib/components/Card.svelte';
  import LikeButton from '$lib/components/LikeButton.svelte';
  import SaveButton from '$lib/components/SaveButton.svelte';
  import type { UserResponse } from '$lib/api/types';

  // Shape of a forum post as used in this component
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

  export let post: Post;
</script>

<!-- Main container card for a single post -->
<Card class="post-card">
  <!-- =========================
       1. POSTER INFO ROW
       ========================= -->
  <div class="poster">
    <!-- User avatar -->
    <img class="avatar" src={post.author.avatarUrl} alt={post.author.name} />

    <!-- Author name + subtitle/role -->
    <div class="author">
      <div class="name">{post.author.name}</div>
      <div class="subtitle">{post.author.role}</div>
    </div>
  </div>

  <!-- =========================
       2. POST CONTENT
       ========================= -->
  <div class="content">
    <!-- Main text body of the post -->
    <p>{post.body}</p>

    <!-- Optional media section (image OR video) -->
    {#if post.mediaType === 'image' && post.mediaUrl}
      <img class="media" src={post.mediaUrl} alt="Post image" />
    {:else if post.mediaType === 'video' && post.mediaUrl}
      <video class="media" controls>
        <source src={post.mediaUrl} />
      </video>
    {/if}
  </div>

  <!-- =========================
       3. ACTION BUTTON ROW
       ========================= -->
  <div class="actions">
    <!-- Like button with current state -->
    <LikeButton liked={post.liked} count={post.likeCount} />

    <!-- Repost placeholder (functionality not implemented yet) -->
    <button type="button"> Repost </button>

    <!-- Save/bookmark toggle -->
    <SaveButton saved={post.saved} />
  </div>
</Card>

<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->

<!-- TODO: Implement the three-tier layout described above using LikeButton and SaveButton. -->

<style>
  /* Overall layout of the post card */
  .post-card {
    display: flex;
    flex-direction: column;
    gap: 0.75rem; /* spacing between poster, content, actions */
  }

  /* Top row: avatar + author info */
  .poster {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  /* Circular avatar styling */
  .avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    object-fit: cover;
  }

  /* Author text container */
  .author .name {
    font-weight: 600;
  }

  .author .subtitle {
    font-size: 0.85rem;
    opacity: 0.7;
  }

  /* Post text */
  .content p {
    margin: 0;
  }

  /* Shared styling for image/video media */
  .media {
    margin-top: 0.75rem;
    width: 100%;
    border-radius: 8px;
  }

  /* Bottom action row */
  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
</style>
