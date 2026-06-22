<!--
  AgeGateNotice
  Purpose: Banner shown in place of hidden social features for users below the required age
    tier, explaining why those features aren't available to them yet. This is a UX courtesy,
    NOT the enforcement mechanism — actual access control must happen server-side per
    CLAUDE.md's age-tier rules.
  Used in: Forum-adjacent surfaces for Exploring tier (11–13) users, and in place of write
    actions (PostComposer) for Learning tier (14–16) users.
  Props:
    - currentTier ('exploring' | 'learning' | 'career'): the user's current age tier
    - requiredTier ('learning' | 'career'): the minimum tier needed for the gated feature
  Behaviour:
    Render a different message depending on the gap, e.g.:
    - exploring → learning: "Social features unlock once you turn 14."
    - exploring/learning → career: "Posting unlocks once you turn 17."
  Styling:
    Muted, non-alarming banner — background #21262d, color #8b949e, border-radius 6px,
    padding 1rem, centered text.
-->
<script lang="ts">
  export let currentTier: 'exploring' | 'learning' | 'career';
  export let requiredTier: 'learning' | 'career';
</script>

<!-- TODO: Implement the messaging logic and banner styling described above. -->
