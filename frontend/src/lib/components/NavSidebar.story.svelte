<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import NavSidebar from './NavSidebar.svelte';

  export let Hst: Hst;

  const links = [
    { label: 'Cloud Computing', href: '#cloud-computing' },
    { label: 'Digital Production', href: '#digital-production' },
  ];
</script>

<Hst.Story title="NavSidebar">
  <Hst.Variant title="Default">
    <div style="height: 500px;">
      <NavSidebar {links} activeHref="#cloud-computing" />
    </div>
  </Hst.Variant>
</Hst.Story>
