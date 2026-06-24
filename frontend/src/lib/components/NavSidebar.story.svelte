<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { TopicResponse, UserResponse } from '$lib/api/types';
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

  const user: UserResponse = {
    id: 1,
    cognito_sub: 'sub-1',
    email: 'student@example.com',
    first_name: 'Jordan',
    last_name: 'Smith',
    created_at: new Date().toISOString(),
  };
</script>

<Hst.Story title="NavSidebar">
  <Hst.Variant title="Logged in">
    <div style="height: 500px;">
      <NavSidebar {user} {topics} activePath="/topics/cloud-computing" />
    </div>
  </Hst.Variant>

  <Hst.Variant title="Guest">
    <div style="height: 500px;">
      <NavSidebar user={null} {topics} activePath="/dashboard" />
    </div>
  </Hst.Variant>
</Hst.Story>
