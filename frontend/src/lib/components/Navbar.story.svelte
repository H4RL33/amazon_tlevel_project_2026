<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import Navbar from './Navbar.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="Navbar">
  <Hst.Variant title="Default">
    <Navbar />
  </Hst.Variant>
</Hst.Story>
