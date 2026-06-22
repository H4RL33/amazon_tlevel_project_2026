<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
</script>

<footer>
  <div class="columns">
    <div class="column">
      <h3 class="column-heading">Navigation</h3>
      <div class="column-links">
        <NavLink href="/" label="Home" />
        <NavLink href="/learn" label="Learn" />
        <NavLink href="/topics" label="Topics" />
        <NavLink href="/dashboard" label="Dashboard" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">About</h3>
      <div class="column-links">
        <NavLink href="#" label="About This Project" />
        <NavLink href="#" label="T-Level Programme" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">Support</h3>
      <div class="column-links">
        <NavLink href="#" label="Help" />
        <NavLink href="#" label="Contact Us" />
      </div>
    </div>
  </div>
  <div class="bottom-bar">
    <p>© 2026 Amazon T-Level Project</p>
  </div>
</footer>

<style>
  footer {
    background: #232f3e;
    color: #ffffff;
    padding: 2rem 1.5rem 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .columns {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    padding-bottom: 2rem;
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .column-heading {
    margin: 0 0 0.75rem;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #ff9900;
  }

  .column-links {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .bottom-bar {
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    padding: 1rem 0;
    text-align: center;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }

  .bottom-bar p {
    margin: 0;
  }
</style>
