<script lang="ts">
  export let href: string;
  export let label: string;
  // Whether this link represents the current page. Shows a permanent underline and bold text.
  export let active = false;
  // Opt-in muted colour for contexts (e.g. Sidebar) that want inactive links to read as grey.
  // `active` always wins over `muted`.
  export let muted = false;
</script>

<a {href} class:muted class:active>{label}</a>

<style>
  a {
    position: relative;
    display: inline-block;
    color: #232f3e;
    text-decoration: none;
    font-family: 'Ubuntu', sans-serif;
  }

  a.muted {
    color: #5a6472;
  }

  a::after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -0.3em;
    width: 100%;
    height: 0.15em;
    border-radius: 0;
    background: #000000;
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease-in-out;
  }

  a:hover::after,
  a.active::after {
    transform: scaleX(1);
  }

  a.active {
    color: #232f3e;
    font-weight: 700;
  }
</style>
