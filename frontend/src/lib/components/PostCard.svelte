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
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

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

<!-- TODO: Implement the three-tier layout described above using LikeButton and SaveButton. -->
