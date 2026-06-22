<!--
  UserProfileHeader
  Purpose: LinkedIn-style profile banner — background image, avatar, name, and subtitle/role.
  Used in: User profile page
  Props:
    - user (UserResponse): the profile owner
    - backgroundImageUrl (string | null): banner image, falls back to a gradient if null
    - avatarUrl (string | null): falls back to initials if null
    - subtitle (string): e.g. role, age tier label, or "AWS Mentor"
    - isMentor (boolean): when true, render a MentorBadge next to the name
  Layout:
    Full-width banner image/gradient, avatar overlapping the bottom-left of the banner,
    name + subtitle below the avatar. MentorBadge inline with the name when isMentor.
  Styling:
    Banner height ~200px, avatar 96px circle with a border matching the page background
    (to "cut out" of the banner), object-fit cover throughout.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';
  import MentorBadge from '$lib/components/MentorBadge.svelte';

  export let user: UserResponse;
  export let backgroundImageUrl: string | null;
  export let avatarUrl: string | null;
  export let subtitle: string;
  export let isMentor = false;
</script>

<!-- TODO: Implement banner + overlapping avatar + name/subtitle layout. Render MentorBadge when isMentor. -->
