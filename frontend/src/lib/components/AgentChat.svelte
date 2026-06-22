<!--
  AgentChat
  Purpose: Teaser input field for the Dynamic Mentor, shown at the bottom of the CTASidebar.
    Clicking/submitting should navigate to the full AgentChatWindow (in The Library), not render
    a conversation inline.
  Used in: CTASidebar
  Props:
    - placeholder (string | undefined): CTA placeholder text, defaults to something like
      "Ask your mentor anything..."
  Behaviour:
    On submit, navigate to /library (or wherever AgentChatWindow lives) with the typed message
    carried over — TODO: decide exact hand-off mechanism (query param, store, etc).
  Styling:
    Plain white background, rectangular, accent line along the bottom in the orange-yellow
    gradient: linear-gradient(to right, #ff9900, #ffd700).
-->
<script lang="ts">
  export let placeholder = 'Ask your mentor anything...';
</script>

<!-- TODO: Implement input field with bottom accent line. Handle submit per the hand-off TODO above. -->
