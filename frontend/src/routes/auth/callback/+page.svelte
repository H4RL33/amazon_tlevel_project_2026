<!--
  Auth Callback — /auth/callback
  Public. Receives Cognito redirect after login.
  Purpose: Exchange the Cognito authorization code for tokens, sync user to DB, then redirect.
  Query param: ?code=<authorization_code>
  Implementation steps:
    1. On mount: read `code` from $page.url.searchParams.get('code').
       If code is null: show error "No authorization code received."
    2. Call exchangeCode(code) from $lib/api/auth.ts.
       This stores id_token in localStorage and returns the token response.
    3. Decode the id_token JWT (base64 decode the payload — no verification needed client-side,
       the backend verifies). Extract `email` from payload.given_name / family_name if present.
    4. Call syncUser(firstName, lastName) — use payload.given_name and family_name from the token,
       or fallback to empty strings if not present (user can set them in settings).
    5. Call getUserTopics() from $lib/api/topics.ts (GET /users/me/topics).
       If the result is an empty array: goto('/onboarding').
       Otherwise: goto('/dashboard').
  Error handling:
    Catch any error from steps 2–5. Show an error message with a link back to / for retry.
  Styling:
    Centred loading spinner during exchange. Dark background (#0d1117).
    Error state: red text with "Something went wrong. Try again." and a link to /.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { exchangeCode, syncUser } from '$lib/api/auth';
  import { getUserTopics } from '$lib/api/topics';

  let error = '';
  let loading = true;

  onMount(async () => {
    // TODO: Implement token exchange flow (see steps in comment above).
  });
</script>

<!-- TODO: Show loading spinner while loading=true. Show error message if error is set. -->
