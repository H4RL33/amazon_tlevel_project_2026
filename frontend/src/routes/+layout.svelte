<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import Footer from '$lib/components/Footer.svelte';
</script>

<Navbar />
<slot />
<Footer />

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
    background: #f5f5f0;
    color: #232f3e;
  }
</style>
