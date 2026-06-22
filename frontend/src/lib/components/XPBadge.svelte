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

<!-- TODO: Implement "+{xp} XP" pill with the earned/available styling distinction above. -->
