<!--
  XPBadge
  Purpose: Small inline indicator showing XP earned or available for reading a given Snippet,
    reinforcing the gamified progression loop.
  Used in: SnippetCard
  Props:
    - xp (number): the XP value to display
    - earned (boolean | undefined): if true, style as "already earned" (muted) rather than
      "available" (highlighted). Defaults to false.
  Styling:
    Small pill, e.g. "+{xp} XP", background in the orange-yellow gradient when earned=false,
    muted grey background when earned=true.
-->
<script lang="ts">
  export let xp: number;
  export let earned = false;
</script>

<span
  class="xp-badge"
  class:earned 
  aria-label={`${xp} XP ${earned ? 'earned' : 'available'}`}
>
  +{xp} XP
</span>
<!-- " class="xp-badge" " applies the CSS class -->
<!-- " class:earned " is short for class:earned={earned} and checks the value of the variable if its true or values. -->
<!-- the aria -label is for accessibility -->

<style>
  .xp-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;

    /* Available (highlighted) */
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: white;
  }

  .xp-badge.earned {
    /* Already earned (muted) */
    background: #e5e7eb;
    color: #6b7280;
  }
</style>




<!-- "<span>" applies styling, scripting, or structure to a specific portion of text or inline content -->
<!-- TODO: Implement "+{xp} XP" pill with the earned/available styling distinction above. -->
