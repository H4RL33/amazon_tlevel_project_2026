<!--
  NavBarAvatar
  Purpose: User avatar shown on the right of the NavBar with a dropdown for the
    user's Settings, Help, and Sign out.
  Used in: NavBar
  Props:
    - user (UserResponse): current user
  Behaviour:
    - Clicking the avatar toggles a dropdown panel anchored below-right of the avatar.
    - Dropdown items: "Settings" (/settings), "Help" (/help), "Sign out".
    - Clicking outside the dropdown or pressing Escape closes it.
  Styling:
    Avatar: 36px circle (via AvatarBadge).
    Dropdown: white background, omnidirectional drop shadow matching PageCard/AlbumCard,
    NavLink components for nav items, matching button style for Sign out.
-->
<script lang="ts">
  import { goto, afterNavigate } from '$app/navigation';
  import { signOut } from '$lib/api/auth';
  import { currentUser } from '$lib/stores/user';
  import type { UserResponse } from '$lib/api/types';
  import AvatarBadge from '$lib/components/AvatarBadge.svelte';
  import NavLink from '$lib/components/NavLink.svelte';

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

  afterNavigate(() => {
    open = false;
  });

  function handleSignOut() {
    signOut();
    currentUser.set(null);
    goto('/');
  }
</script>

<svelte:window on:click={handleWindowClick} on:keydown={handleKeydown} />

<div class="avatar-container" bind:this={containerEl}>
  <button class="avatar-button" on:click={toggle} aria-label="User menu" aria-expanded={open}>
    <AvatarBadge {user} size="36px" />
  </button>

  {#if open}
    <div class="dropdown">
      <div class="dropdown-item"><NavLink href="/settings" label="Settings" /></div>
      <div class="dropdown-item"><NavLink href="/help" label="Help" /></div>
      <hr class="divider" />
      <button class="sign-out" on:click={handleSignOut}>Sign out</button>
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
    display: flex;
    align-items: center;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    min-width: 180px;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
    z-index: 10;
  }

  .dropdown-item {
    padding: 0.5rem 1rem;
    display: block;
    font-size: 0.875rem;
  }

  .dropdown-item :global(a) {
    display: block;
    width: 100%;
  }

  .divider {
    border: none;
    border-top: 1px solid #e2e2dc;
    margin: 0.25rem 0;
  }

  .sign-out {
    background: none;
    border: none;
    cursor: pointer;
    width: 100%;
    text-align: left;
    color: #232f3e;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-family: 'Ubuntu', sans-serif;
  }

  .sign-out:hover {
    text-decoration: underline;
  }
</style>
