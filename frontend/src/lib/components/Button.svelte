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

<button
  {type}
  {disabled}
  class={variant}
  on:click
>
  <slot />
</button>

<style>
  button {
    font-family: 'Ubuntu', sans-serif;
    border-radius: 6px;
    padding: 0.5rem 1.25rem;
    font-size: 0.875rem;
    cursor: pointer;
    border: none;
    color: #ffffff;
    transition: opacity 0.15s;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .primary {
    background: #1f6feb;
  }

  .secondary {
    background: #21262d;
  }

  .danger {
    background: #ef4444;
  }
</style>
