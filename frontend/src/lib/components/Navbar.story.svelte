<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { UserResponse } from '$lib/api/types';
  import Navbar from './Navbar.svelte';
  import { currentUser } from '$lib/stores/user';

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

  currentUser.set(user);
</script>

<Hst.Story title="Navbar">
  <Hst.Variant title="Logged in">
    <Navbar />
  </Hst.Variant>
</Hst.Story>
