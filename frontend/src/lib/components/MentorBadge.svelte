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
  // The badge can be shown in a smaller inline spot or a regular size.
  export let size: 'sm' | 'md' = 'md';
</script>

<span class={`mentor-badge ${size}`} aria-label="AWS Mentor">
  AWS Mentor
</span>

<style>
  .mentor-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: #232f3e;
    color: #ff9900;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .md {
    padding: 0.35rem 0.65rem;
    font-size: 0.75rem;
  }

  .sm {
    padding: 0.2rem 0.5rem;
    font-size: 0.65rem;
  }
</style>
