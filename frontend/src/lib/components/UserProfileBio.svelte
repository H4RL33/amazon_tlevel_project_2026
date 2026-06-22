<!--
  UserProfileBio
  Purpose: Free-text bio shown directly under UserProfileHeader.
  Used in: User profile page
  Props:
    - bio (string): plain text, max 500 characters (enforce/trim server-side; this component
      just renders it)
  Styling:
    Plain paragraph text, line-height 1.6, max-width matching UserProfileHeader's content width.
-->
<script lang="ts">
  export let bio: string;
</script>

<!-- TODO: Render bio as plain text. Show nothing (or an empty-state) if bio is an empty string. -->
