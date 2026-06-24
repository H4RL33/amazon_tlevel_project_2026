<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import NavLink from './NavLink.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="NavLink">
  <Hst.Variant title="Default">
    <div style="background: #232f3e; padding: 1rem;">
      <NavLink href="/learn" label="Learn" />
    </div>
  </Hst.Variant>
</Hst.Story>
