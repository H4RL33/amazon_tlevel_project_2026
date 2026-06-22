<script lang="ts">
  export let href: string;
  export let label: string;
</script>

<a {href}>{label}</a>

<style>
  a {
    position: relative;
    display: inline-block;
    color: #ffffff;
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
    border-radius: 9999px;
    background: linear-gradient(to right, #ff9900, #ffd700);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease-in-out;
  }

  a:hover::after {
    transform: scaleX(1);
  }
</style>
