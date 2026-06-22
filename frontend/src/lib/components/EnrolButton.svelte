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
  export let albumId: number;
  export let enrolled: boolean;
  export let isAuthenticated: boolean;
</script>

<!-- TODO: Implement the three behaviours above using the Button component. -->
