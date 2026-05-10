<!--
  Settings — /settings
  Protected.
  Purpose: Allow user to update their name and change topic interests.
  Sections:
    1. "Profile" — first_name and last_name fields (text inputs), save via PATCH /users/me
       (add this endpoint to the backend users router if needed).
    2. "Topic Interests" — TopicGrid in selectable mode, pre-selected with current $userTopics.
       Save via PUT /users/me/topics.
  Behaviour:
    - Pre-populate inputs from $currentUser store.
    - Show success/error feedback after each save.
  Styling: max-width 600px, margin auto, padding 1.5rem. Section headings use h2.
-->
<script lang="ts">
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import Button from '$lib/components/Button.svelte';
  import { currentUser, userTopics } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';

  let firstName = $currentUser?.first_name ?? '';
  let lastName = $currentUser?.last_name ?? '';
  let selectedTopicIds: number[] = $userTopics.map((t) => t.id);
</script>

<svelte:head><title>Settings — AWS Academy</title></svelte:head>

<!-- TODO: Implement profile form and topic interest selection with save buttons. -->
