<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import Footer from './Footer.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="Footer">
  <Hst.Variant title="Default">
    <Footer />
  </Hst.Variant>
</Hst.Story>
