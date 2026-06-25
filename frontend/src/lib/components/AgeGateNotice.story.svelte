<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import AgeGateNotice from './AgeGateNotice.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="AgeGateNotice">
  <Hst.Variant title="Exploring → Learning">
    <AgeGateNotice currentTier="exploring" requiredTier="learning" />
  </Hst.Variant>

  <Hst.Variant title="Exploring → Career">
    <AgeGateNotice currentTier="exploring" requiredTier="career" />
  </Hst.Variant>

  <Hst.Variant title="Learning → Career">
    <AgeGateNotice currentTier="learning" requiredTier="career" />
  </Hst.Variant>
</Hst.Story>
