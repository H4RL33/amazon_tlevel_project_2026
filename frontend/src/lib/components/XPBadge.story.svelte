<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import XPBadge from './XPBadge.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="XPBadge">
  <Hst.Variant title="Available">
    <XPBadge xp={50} />
  </Hst.Variant>

  <Hst.Variant title="Earned">
    <XPBadge xp={50} earned />
  </Hst.Variant>
</Hst.Story>
