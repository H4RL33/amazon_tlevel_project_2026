<!--
  App Layout — wraps all /(app)/* routes
  Purpose: Client-side auth guard + mounts AppShell with stores populated.
  Behaviour on mount:
    1. Check localStorage for 'id_token'. If absent: goto('/').
    2. Call listTopics() and store result in $allTopics.
    3. Call GET /users/me and store result in $currentUser.
    4. Call getProgress() and store result in $continueReading.
    If any API call returns 401: clear localStorage, goto('/').
  Styling: none — AppShell handles layout.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import AppShell from '$lib/components/AppShell.svelte';
  import { listTopics } from '$lib/api/topics';
  import { getProgress } from '$lib/api/progress';
  import { apiFetch } from '$lib/api/client';
  import { ApiError } from '$lib/api/client';
  import type { UserResponse } from '$lib/api/types';
  import { currentUser } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';
  import { continueReading } from '$lib/stores/progress';

  onMount(async () => {
    if (!localStorage.getItem('id_token')) {
      goto('/');
      return;
    }
    try {
      const [topics, user, progress] = await Promise.all([
        listTopics(),
        apiFetch<UserResponse>('/users/me'),
        getProgress(),
      ]);
      allTopics.set(topics);
      currentUser.set(user);
      continueReading.set(progress);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        localStorage.removeItem('id_token');
        goto('/');
      }
    }
  });
</script>

<AppShell>
  <slot />
</AppShell>
