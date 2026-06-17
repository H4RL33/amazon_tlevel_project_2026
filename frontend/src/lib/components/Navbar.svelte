<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
</script>

<nav>
  <a href="/" class="logo-link">
    <img src="/assets/logo.png" alt="T Level Placements at Amazon" class="logo" />
  </a>
  <div class="links">
    <NavLink href="/" label="Home" />
    <NavLink href="/learn" label="Learn" />
    <NavLink href="/topics" label="Topics" />
    <NavLink href="/dashboard" label="Dashboard" />
  </div>
</nav>

<style>
  nav {
    display: flex;
    align-items: center;
    background: #232f3e;
    padding: 0 1.5rem;
    height: 64px;
    width: 100%;
    box-sizing: border-box;
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
