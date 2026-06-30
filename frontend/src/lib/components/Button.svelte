<!--
  Button
  Purpose: Standard interactive button with variant styles.
  Used in: All pages — forms, CTAs, actions.
  Props:
    - variant ('primary' | 'secondary' | 'danger' | 'cta'): visual style.
      All variants share the design-system base: white background, border-radius 0,
      omnidirectional drop shadow, dark text (#232f3e). Variants differ by hover underline colour:
        primary   = underline colour #1f6feb (AWS blue)
        secondary = underline colour #5a6472 (muted grey)
        danger    = text and underline colour #ef4444 (red)
        cta       = white surface with drop shadow and dark text (matches home page hero CTA)
    - disabled (boolean): disables interaction, reduces opacity to 0.5
    - type ('button' | 'submit' | 'reset'): HTML button type, default 'button'
  Slots: default — button label text or content
  Events: forwards native 'click' event to parent
  Styling: border-radius 0, padding 0.5rem 1.25rem, font-size 0.875rem, cursor pointer
-->
<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'danger' | 'cta' = 'primary';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
</script>

<button {type} {disabled} class={variant} on:click {...$$restProps}>
  <slot />
</button>

<style>
  button {
    font-family: 'Ubuntu', sans-serif;
    border-radius: 0;
    padding: 0.5rem 1.25rem;
    font-size: 0.875rem;
    cursor: pointer;
    border: none;
    background: #ffffff;
    color: #232f3e;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    text-decoration: none;
    transition: text-decoration-color 0.15s;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .primary:hover:not(:disabled),
  .primary:focus-visible:not(:disabled) {
    text-decoration: underline;
    text-decoration-color: #1f6feb;
  }

  .secondary:hover:not(:disabled),
  .secondary:focus-visible:not(:disabled) {
    text-decoration: underline;
    text-decoration-color: #5a6472;
  }

  .danger {
    color: #ef4444;
  }

  .danger:hover:not(:disabled),
  .danger:focus-visible:not(:disabled) {
    text-decoration: underline;
    text-decoration-color: #ef4444;
  }

  .cta {
    background: #ffffff;
    color: #232f3e;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
  }
</style>
