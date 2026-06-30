<!--
  EnrolButton
  Purpose: CTA button on an Album view used to enrol in it.
  Used in: Album view
  Props:
    - albumId (number): the Album to enrol in
    - enrolled (boolean): if already enrolled, render as a disabled/"Enrolled" state instead
    - isAuthenticated (boolean): if false, clicking should redirect to login/registration
      instead of calling the enrol API
  Behaviour:
    - If !isAuthenticated: clicking navigates to the login flow (TODO: confirm exact route,
      likely Cognito hosted UI redirect).
    - If isAuthenticated && !enrolled: clicking calls an enrol API (TODO: define once the
      Album model and an `/albums/{id}/enrol` endpoint exist) and flips to the enrolled state.
  Styling:
    Use the Button component, variant="primary". Enrolled state: variant="secondary", disabled.
-->
<script lang="ts">
  import { getCognitoLoginUrl } from '$lib/api/auth';
  import { enrolAlbum } from '$lib/api/albums';
  import Button from '$lib/components/Button.svelte';

  export let albumId: number;
  export let enrolled: boolean;
  export let isAuthenticated: boolean;

  let isSubmitting = false;
  let hasEnrolled = enrolled;

  async function handleClick() {
    if (!isAuthenticated) {
      window.location.href = await getCognitoLoginUrl();
      return;
    }

    if (hasEnrolled || isSubmitting) {
      return;
    }

    isSubmitting = true;

    try {
      await enrolAlbum(albumId);
      hasEnrolled = true;
    } finally {
      isSubmitting = false;
    }
  }
</script>

<Button
  variant={hasEnrolled ? 'secondary' : 'primary'}
  disabled={hasEnrolled || isSubmitting}
  type="button"
  on:click={handleClick}
>
  {#if hasEnrolled}
    Enrolled
  {:else if isSubmitting}
    Enrolling...
  {:else}
    Enrol now
  {/if}
</Button>
