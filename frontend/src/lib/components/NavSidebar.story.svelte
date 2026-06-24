<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { TopicResponse } from '$lib/api/types';
  import NavSidebar from './NavSidebar.svelte';

  export let Hst: Hst;

  const topics: TopicResponse[] = [
    {
      id: 1,
      slug: 'cloud-computing',
      name: 'Cloud Computing',
      description: '',
      accent_colour: '#1f6feb',
    },
    {
      id: 2,
      slug: 'digital-production',
      name: 'Digital Production',
      description: '',
      accent_colour: '#ff9900',
    },
  ];
</script>

<Hst.Story title="NavSidebar">
  <Hst.Variant title="Default">
    <div style="height: 500px;">
      <NavSidebar {topics} activePath="/topics/cloud-computing" />
    </div>
  </Hst.Variant>
</Hst.Story>
