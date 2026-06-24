<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import Button from './Button.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="Button">
  <Hst.Variant title="Primary">
    <Button variant="primary">Primary</Button>
  </Hst.Variant>

  <Hst.Variant title="Secondary">
    <Button variant="secondary">Secondary</Button>
  </Hst.Variant>

  <Hst.Variant title="Danger">
    <Button variant="danger">Danger</Button>
  </Hst.Variant>

  <Hst.Variant title="Disabled">
    <Button variant="primary" disabled>Disabled</Button>
  </Hst.Variant>
</Hst.Story>
