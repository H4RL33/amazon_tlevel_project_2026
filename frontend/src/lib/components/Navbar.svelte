<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import NavBarAvatar from '$lib/components/NavBarAvatar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { currentUser } from '$lib/stores/user';
</script>

<PageCard as="nav" padding="0 1.5rem">
  <div class="nav-inner">
    <a href="/" class="logo-link">
      <img src="/assets/logo.png" alt="T Level Placements at Amazon" class="logo" />
    </a>
    <div class="links">
      <NavLink href="/" label="Home" />
      <NavLink href="/learn" label="Learn" />
      <NavLink href="/topics" label="Topics" />
      <NavLink href={$currentUser ? '/library' : '/login'} label="Library" />
      <NavLink href={$currentUser ? '/dashboard' : '/login'} label="Dashboard" />
      {#if $currentUser}
        <NavBarAvatar user={$currentUser} />
      {:else}
        <NavLink href="/login" label="Log in" />
      {/if}
    </div>
  </div>
</PageCard>

<style>
  .nav-inner {
    display: flex;
    align-items: center;
    height: 64px;
    width: 100%;
  }

  .logo-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    flex-shrink: 0;
  }

  .logo {
    height: 40px;
  }

  .links {
    margin-left: auto;
    display: flex;
    gap: 1.5rem;
    align-items: center;
    overflow: visible;
  }
</style>
