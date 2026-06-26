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
  // Changes ----------------------
  import { createEventDispatcher } from 'svelte';

  export let placeholder = 'Ask your mentor anything...';

  const dispatch = createEventDispatcher<{
    submit: string;
  }>();

  let message = '';

  function handle_submit() {
    const trimmed = message.trim(); // validates text and prevents empty messages like blank spaces

    if (!trimmed) return;

    dispatch('submit', trimmed); // hands the the message to the parent

    message = '';
  }
</script>

<form class="agent-chat" on:submit|preventDefault={handle_submit}>
  <!-- this is for allowing the user to press 
  enter or click send and "preventDefault" stops the browser from reloading the page. -->
  <input bind:value={message} type="text" {placeholder} autocomplete="off" />
  <!-- the input is bound to the variable "message" so the input is stored in that variable -->
  <button type="submit" aria-label="Send"> </button>
</form>

<!-- Changes ------------------------>

<!-- TODO: Implement input field with bottom accent line. Handle submit per the hand-off TODO above. -->

<style>
  .agent-chat {
    display: flex;
    align-items: center;
    background: white;
    border-radius: 0;
    border-bottom: 3px solid transparent;
    border-image: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700)) 1;
  }

  input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.875rem 1rem;
    font-size: 0.95rem;
    background: transparent;

    color: black;
  }

  button {
    border: none;
    background: transparent;
    padding: 0 1rem;
    cursor: pointer;
    font-size: 1rem;
  }
</style>
