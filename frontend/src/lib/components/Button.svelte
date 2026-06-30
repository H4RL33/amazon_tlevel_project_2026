<!--
  Button
  Purpose: Standard interactive button with variant styles.
  Used in: All pages — forms, CTAs, actions.
  Props:
    - variant ('primary' | 'secondary' | 'danger'): visual style.
      primary = AWS blue (#1f6feb), secondary = muted surface (#21262d), danger = red (#ef4444)
    - disabled (boolean): disables interaction, reduces opacity to 0.5
    - type ('button' | 'submit' | 'reset'): HTML button type, default 'button'
  Slots: default — button label text or content
  Events: forwards native 'click' event to parent
  Styling: border-radius 6px, padding 0.5rem 1.25rem, font-size 0.875rem, cursor pointer
-->
<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'danger' = 'primary';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
</script>

<button {type} {disabled} class={variant} on:click>
  <slot />
</button>

<style>
  button {
    border-radius: 6px;
    padding: 0.5rem 1.25rem;
    font-size: 0.875rem;
    font-family: 'Ubuntu', sans-serif;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition:
      opacity 0.15s,
      filter 0.15s;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  button:not(:disabled):hover {
    filter: brightness(1.1);
  }

  .primary {
    background: #1f6feb;
    color: #ffffff;
  }

  .secondary {
    background: #21262d;
    color: #ffffff;
  }

  .danger {
    background: #ef4444;
    color: #ffffff;
  }
</style>
