<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Navbar from '$lib/components/Navbar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import { getPagePalette } from '$lib/gradient';
  import { TOKEN_KEY } from '$lib/api/client';
  import { getMe } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  type Layer = { palette: [string, string, string]; visible: boolean };

  const initialPalette = getPagePalette($page.url.pathname);
  let layers: [Layer, Layer] = [
    { palette: initialPalette, visible: true },
    { palette: initialPalette, visible: false },
  ];
  let activeIndex = 0;

  onMount(async () => {
    if (localStorage.getItem(TOKEN_KEY)) {
      try {
        currentUser.set(await getMe());
      } catch (err) {
        console.error('Failed to rehydrate current user:', err);
        localStorage.removeItem(TOKEN_KEY);
      }
    }
  });

  $: {
    const next = getPagePalette($page.url.pathname);
    if (next.join('|') !== layers[activeIndex].palette.join('|')) {
      const inactiveIndex = activeIndex === 0 ? 1 : 0;
      layers[inactiveIndex] = { palette: next, visible: true };
      layers[activeIndex] = { ...layers[activeIndex], visible: false };
      activeIndex = inactiveIndex;
      layers = layers;
    }
  }
  $: morphingBackdrop = $page.url.pathname === '/' && !$currentUser;
</script>

<div class="backdrop" aria-hidden="true">
  {#each layers as layer, i (i)}
    <div
      class="layer"
      class:visible={layer.visible}
      class:morphing={morphingBackdrop && i === activeIndex}
    >
      <div
        class="blob blob-a"
        style="background: radial-gradient(circle, {layer.palette[0]}, transparent 70%);"
      ></div>
      <div
        class="blob blob-b"
        style="background: radial-gradient(circle, {layer.palette[1]}, transparent 70%);"
      ></div>
      <div
        class="blob blob-c"
        style="background: radial-gradient(circle, {layer.palette[2]}, transparent 70%);"
      ></div>
    </div>
  {/each}
</div>

<div
  class="shell"
  style="--page-p0: {layers[activeIndex].palette[0]}; --page-p1: {layers[activeIndex].palette[1]};"
>
  <Navbar />
  <div class="content">
    <slot />
  </div>
  <Footer />
</div>

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(html, body) {
    height: 100%;
  }

  :global(body) {
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
    background: #f5f5f0;
    color: #232f3e;
  }

  :global(:root) {
    --gap-inner: 1.5rem;
    --gap-outer: 2.25rem;
  }

  .backdrop {
    position: fixed;
    inset: 0;
    z-index: -1;
    overflow: hidden;
    background: #f5f5f0;
  }

  .layer {
    position: absolute;
    inset: 0;
    opacity: 0;
    transition: opacity 1.2s ease;
  }

  .layer.visible {
    opacity: 1;
  }

  .layer.morphing {
    animation: morph-hue 8s linear infinite;
  }

  @keyframes morph-hue {
    from {
      filter: hue-rotate(0deg);
    }
    to {
      filter: hue-rotate(360deg);
    }
  }

  .blob {
    position: absolute;
    width: 70vmax;
    height: 70vmax;
    border-radius: 50%;
    filter: blur(40px);
    opacity: 0.6;
  }

  .blob-a {
    top: -15%;
    left: -15%;
    animation: drift-a 28s ease-in-out infinite;
  }

  .blob-b {
    top: -10%;
    right: -20%;
    animation: drift-b 34s ease-in-out infinite;
  }

  .blob-c {
    bottom: -20%;
    left: 15%;
    animation: drift-c 40s ease-in-out infinite;
  }

  @keyframes drift-a {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(8vmax, 6vmax);
    }
  }

  @keyframes drift-b {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(-6vmax, 8vmax);
    }
  }

  @keyframes drift-c {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(5vmax, -7vmax);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .blob {
      animation: none;
    }

    .layer {
      transition: none;
    }

    .layer.morphing {
      animation: none;
    }
  }

  .shell {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100vh;
    box-sizing: border-box;
    padding: var(--gap-outer);
    gap: var(--gap-inner);
  }

  /* Navbar/Footer keep their own content-driven height (flex's default
     0 1 auto) and never move. This is the one scrollable region — capped to
     whatever's left of the 100vh shell via min-height: 0, which overrides
     flex's default min-height: auto that would otherwise let it grow past
     that and push the footer down. */
  .content {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }
</style>
