<!--
  Onboarding — /onboarding
  Protected. Shown to first-time users after Cognito login.
  Purpose: Let the user select their topic interests before reaching the dashboard.
  Behaviour:
    1. Render TopicGrid with selectable=true.
    2. Show a "Continue" Button (disabled until at least 1 topic is selected).
    3. On submit: call PUT /users/me/topics with selected topic ids via setTopics().
       On success: goto('/dashboard').
  Heading: "What are you interested in?" — subtext: "Choose at least one topic area to personalise your experience."
  Styling:
    Centred content, max-width 700px, margin auto. No sidebar needed (but AppShell wraps it).
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { apiFetch } from '$lib/api/client';
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import Button from '$lib/components/Button.svelte';
  import { allTopics } from '$lib/stores/topics';

  let selectedIds: number[] = [];

  async function submit() {
    // TODO: Call PUT /users/me/topics with selectedIds, then goto('/dashboard')
  }
</script>

<!-- TODO: Implement onboarding page with TopicGrid (selectable) and submit button. -->
