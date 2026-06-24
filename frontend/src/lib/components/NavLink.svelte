<script lang="ts">
  export let href: string;
  export let label: string;
</script>

<a {href}>{label}</a>

<style>
  a {
    position: relative;
    display: inline-block;
    color: #232f3e;
    text-decoration: none;
    font-family: 'Ubuntu', sans-serif;
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

  a:hover::after {
    transform: scaleX(1);
  }
</style>
