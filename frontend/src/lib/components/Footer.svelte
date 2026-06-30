<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="footer" padding="2rem 1.5rem 0">
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
</PageCard>

<style>
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
    color: #000000;
  }

  .column-links {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .bottom-bar {
    border-top: 1px solid rgba(35, 47, 62, 0.15);
    padding: 1rem 0;
    text-align: center;
    font-size: 0.85rem;
    color: #5a6472;
  }

  .bottom-bar p {
    margin: 0;
  }
</style>
