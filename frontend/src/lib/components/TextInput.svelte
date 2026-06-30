<script lang="ts">
  export let value = '';
  export let placeholder = '';
  export let label = '';
  export let id = '';
  export let disabled = false;
  export let type = 'text';

  let focused = false;

  function handleInput(e: Event) {
    value = (e.currentTarget as HTMLInputElement).value;
  }
</script>

{#if label}
  <label for={id} class="input-label">{label}</label>
{/if}
<div class="text-input-wrapper" class:focused>
  <input
    {id}
    {type}
    {placeholder}
    {disabled}
    {value}
    on:focus={() => (focused = true)}
    on:blur={() => (focused = false)}
    on:input={handleInput}
    on:change
  />
  <span class="underline" aria-hidden="true"></span>
</div>

<style>
  .input-label {
    display: block;
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #5a6472;
    margin-bottom: 0.5rem;
  }

  .text-input-wrapper {
    position: relative;
    background: #ffffff;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    overflow: hidden;
  }

  input {
    display: block;
    width: 100%;
    box-sizing: border-box;
    border: none;
    outline: none;
    background: transparent;
    padding: 0.75rem 1rem;
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.95rem;
    color: #232f3e;
  }

  input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  input::placeholder {
    color: #9ca3af;
  }

  .underline {
    display: block;
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: #232f3e;
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.2s ease;
  }

  .text-input-wrapper.focused .underline {
    transform: scaleX(1);
  }
</style>
