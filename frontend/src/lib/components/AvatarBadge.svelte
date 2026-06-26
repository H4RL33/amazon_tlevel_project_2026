<!--
  AvatarBadge
  Purpose: Renders a circular avatar — either the user's uploaded photo (avatar_url) or
    a coloured circle with initials derived from first_name/last_name.
  Used in: NavBarAvatar (36px), Settings page (32px).
  Props:
    - user (UserResponse): provides avatar_url, first_name, last_name
    - size (string): CSS length for the circle diameter, default '36px'
  Styling:
    Circle background #1f6feb (initials variant). Image variant: object-fit cover.
    Font-size is ~44% of the numeric size value, set via inline style.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

  export let user: UserResponse;
  export let size: string = '36px';

  $: initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();

  // Parse the numeric portion of the size string (e.g. '36px' → 36) to derive font-size.
  $: numericSize = parseFloat(size);
  $: fontSize = `${(numericSize * 0.44).toFixed(1)}px`;
</script>

{#if user.avatar_url}
  <img
    src={user.avatar_url}
    alt=""
    class="avatar"
    style="width: {size}; height: {size};"
  />
{:else}
  <span
    class="avatar initials"
    style="width: {size}; height: {size}; font-size: {fontSize};"
  >
    {initials}
  </span>
{/if}

<style>
  .avatar {
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    flex-shrink: 0;
  }

  .initials {
    background: #1f6feb;
    color: #ffffff;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  img.avatar {
    object-fit: cover;
  }
</style>
