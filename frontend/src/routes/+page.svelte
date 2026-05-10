<!--
  Landing Page — /
  Public. No auth required.
  Purpose: Entry point for unauthenticated users.
  Contains:
    1. Hero section: platform name "AWS Academy T-Level Guide", tagline, "Get Started" CTA button.
    2. Brief overview row of the 5 topic areas (icons or colour chips).
  Behaviour:
    "Get Started" button href = cognitoLoginUrl (built below).
    If user is already logged in (id_token in localStorage), redirect to /dashboard on mount.
  Cognito login URL format:
    {VITE_COGNITO_DOMAIN}/oauth2/authorize
      ?client_id={VITE_COGNITO_CLIENT_ID}
      &response_type=code
      &scope=openid+profile+email
      &redirect_uri={encodeURIComponent(VITE_COGNITO_REDIRECT_URI)}
  Styling:
    Full-viewport hero, background #0a2540 (dark navy), white heading (font-size 2.5rem),
    muted subtitle (#8b949e), CTA button uses Button variant='primary'.
    No sidebar on this page.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/Button.svelte';
  import { getCognitoLoginUrl } from '$lib/api/auth';
  import { TOKEN_KEY } from '$lib/api/client';

  const cognitoLoginUrl = getCognitoLoginUrl();

  onMount(() => {
    if (localStorage.getItem(TOKEN_KEY)) goto('/dashboard');
  });
</script>

<!-- TODO: Implement hero section with "Get Started" CTA linking to cognitoLoginUrl. -->
