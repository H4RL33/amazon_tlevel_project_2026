<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import HelpPanel from './HelpPanel.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="HelpPanel">
  <Hst.Variant title="Default">
    <HelpPanel />
  </Hst.Variant>
</Hst.Story>
