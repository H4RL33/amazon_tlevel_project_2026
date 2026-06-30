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
  // The bio text passed in from the parent component.
  export let bio: string;
</script>

{#if bio.trim()}
  <!-- Show the bio as normal paragraph text. -->
  <p class="bio">{bio}</p>
{:else}
  <!-- Show nothing when there is no bio to display. -->
  <p class="bio empty">No bio added yet.</p>
{/if}

<style>
  .bio {
    margin: 0;
    line-height: 1.6;
    color: #374151;
  }

  .empty {
    color: #6b7280;
    font-style: italic;
  }
</style>
