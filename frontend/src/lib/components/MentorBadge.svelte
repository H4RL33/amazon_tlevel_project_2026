<!--
  MentorBadge
  Purpose: Small tag/label identifying accounts belonging to AWS mentors, so prospective
    students can recognise them in the Forum and on profiles.
  Used in: UserProfileHeader, PostCard (next to the poster's name)
  Props:
    - size ('sm' | 'md' | undefined): defaults to 'md'. Use 'sm' when shown inline in a
      PostCard's poster row.
  Styling:
    Small pill, e.g. "AWS Mentor", background #232f3e, color #ff9900, font-weight 600,
    font-size 0.65rem (sm) / 0.75rem (md), letter-spacing 0.04em.
-->
<script lang="ts">
  export let size: 'sm' | 'md' = 'md';
</script>

<!-- TODO: Implement "AWS Mentor" pill with the sm/md size variants above. -->
