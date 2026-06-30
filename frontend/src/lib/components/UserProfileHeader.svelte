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

  // Use the first letters of the name if no avatar image is available.
  $: initials = `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase();
</script>

<div class="profile-header">
  <div
    class="banner"
    style={backgroundImageUrl ? `background-image: url(${backgroundImageUrl});` : undefined}
  />

  <div class="profile-info">
    {#if avatarUrl}
      <img class="avatar" src={avatarUrl} alt={`${user.first_name} ${user.last_name}`} />
    {:else}
      <div class="avatar initials" aria-label="Avatar initials">{initials}</div>
    {/if}

    <div class="details">
      <div class="name-row">
        <h2>{user.first_name} {user.last_name}</h2>
        {#if isMentor}
          <MentorBadge size="sm" />
        {/if}
      </div>
      <p class="subtitle">{subtitle}</p>
    </div>
  </div>
</div>

<style>
  .profile-header {
    width: 100%;
  }

  .banner {
    height: 200px;
    background: linear-gradient(135deg, #232f3e 0%, #ff9900 100%);
    background-size: cover;
    background-position: center;
  }

  .profile-info {
    display: flex;
    align-items: flex-end;
    gap: 1rem;
    padding: 0 1.5rem 1.5rem;
    margin-top: -48px;
  }

  .avatar {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    border: 4px solid #ffffff;
    object-fit: cover;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .initials {
    font-weight: 700;
    color: #232f3e;
    font-size: 1.25rem;
  }

  .details {
    padding-bottom: 0.5rem;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  h2 {
    margin: 0;
    color: #232f3e;
  }

  .subtitle {
    margin: 0.25rem 0 0;
    color: #6b7280;
  }
</style>
