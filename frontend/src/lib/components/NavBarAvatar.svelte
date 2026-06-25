<!--
  NavBarAvatar
  Purpose: User avatar shown on the right of the NavBar with a dropdown for the
    user's Dashboard, Settings, and Help.
  Used in: NavBar
  Props:
    - user (UserResponse): current user -- renders the uploaded avatar image when
      user.avatar_url is set, otherwise falls back to initials from first_name/
      last_name on a coloured circle.
  Behaviour:
    - Clicking the avatar toggles a dropdown panel anchored below-right of the avatar.
    - Dropdown items: "Dashboard" (/dashboard), "Settings" (/settings), "Help" (/help).
    - Clicking outside the dropdown or pressing Escape closes it.
  Styling:
    Avatar: 36px circle.
    Dropdown: background #161b22, border 1px solid #21262d, border-radius 8px,
    box-shadow 0 4px 12px rgba(0,0,0,0.4), min-width 180px.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

  export let user: UserResponse;

  let open = false;
  let containerEl: HTMLDivElement;

  function toggle() {
    open = !open;
  }

  function close() {
    open = false;
  }

  function handleWindowClick(event: MouseEvent) {
    if (open && containerEl && !containerEl.contains(event.target as Node)) {
      close();
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (open && event.key === 'Escape') {
      close();
    }
  }

  $: initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();
</script>

<svelte:window on:click={handleWindowClick} on:keydown={handleKeydown} />

<div class="avatar-container" bind:this={containerEl}>
  <button class="avatar-button" on:click={toggle} aria-label="User menu" aria-expanded={open}>
    {#if user.avatar_url}
      <img src={user.avatar_url} alt="" class="avatar avatar-image" />
    {:else}
      <span class="avatar">{initials}</span>
    {/if}
  </button>

  {#if open}
    <div class="dropdown">
      <a href="/dashboard">Dashboard</a>
      <a href="/settings">Settings</a>
      <a href="/help">Help</a>
    </div>
  {/if}
</div>

<style>
  .avatar-container {
    position: relative;
  }

  .avatar-button {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }

  .avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #1f6feb;
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 700;
  }

  .avatar-image {
    object-fit: cover;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    min-width: 180px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
    z-index: 10;
  }

  .dropdown a {
    color: #c9d1d9;
    text-decoration: none;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .dropdown a:hover {
    background: rgba(255, 255, 255, 0.05);
  }
</style>
