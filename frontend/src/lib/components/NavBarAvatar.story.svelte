<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { UserResponse } from '$lib/api/types';
  import NavBarAvatar from './NavBarAvatar.svelte';

  export let Hst: Hst;

  const user: UserResponse = {
    id: 1,
    cognito_sub: 'sub-1',
    email: 'jordan@example.com',
    first_name: 'Jordan',
    last_name: 'Smith',
    avatar_url: null,
    created_at: new Date().toISOString(),
  };
</script>

<Hst.Story title="NavBarAvatar">
  <Hst.Variant title="Default">
    <div style="background: #232f3e; padding: 1rem; display: flex; justify-content: flex-end;">
      <NavBarAvatar {user} />
    </div>
  </Hst.Variant>
</Hst.Story>
