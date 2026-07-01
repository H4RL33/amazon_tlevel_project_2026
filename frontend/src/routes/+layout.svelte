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
</div>
<Footer />

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(html) {
    font-size: 14px;
  }

  :global(html) {
    min-height: 100%;
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
    contain: layout style paint;
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

  .blob {
    position: absolute;
    width: 85vmax;
    height: 85vmax;
    border-radius: 50%;
    filter: blur(20px);
    opacity: 0.6;
  }

  .blob-a {
    top: -15%;
    left: -15%;
  }

  .blob-b {
    top: -10%;
    right: -20%;
  }

  .blob-c {
    bottom: -20%;
    left: 15%;
  }

  .layer.morphing .blob {
    will-change: transform;
    /* Perf: measured ~8fps (vs ~55-60fps with filter removed) when an animated
       `transform` runs on an element with `filter: blur()` applied — the browser
       repaints/refilters the blurred region every frame, which is very costly
       without GPU compositing (e.g. hardened/privacy browsers that disable
       hardware acceleration). Dropping the filter only while actively morphing
       keeps the blur (cheap, static) everywhere else and relies on the radial
       gradient's own soft transparent falloff for edge softness during motion. */
    filter: none;
  }

  .layer.morphing .blob-a {
    animation: drift-a 28s ease-in-out infinite;
  }

  .layer.morphing .blob-b {
    animation: drift-b 34s ease-in-out infinite;
  }

  .layer.morphing .blob-c {
    animation: drift-c 40s ease-in-out infinite;
  }

  @keyframes drift-a {
    0%,
    100% {
      transform: translate3d(0, 0, 0);
    }
    50% {
      transform: translate3d(8vmax, 6vmax, 0);
    }
  }

  @keyframes drift-b {
    0%,
    100% {
      transform: translate3d(0, 0, 0);
    }
    50% {
      transform: translate3d(-6vmax, 8vmax, 0);
    }
  }

  @keyframes drift-c {
    0%,
    100% {
      transform: translate3d(0, 0, 0);
    }
    50% {
      transform: translate3d(5vmax, -7vmax, 0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .blob,
    .layer.morphing .blob-a,
    .layer.morphing .blob-b,
    .layer.morphing .blob-c {
      animation: none;
    }

    .layer {
      transition: none;
    }
  }

  .shell {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100dvh;
    box-sizing: border-box;
    /* Symmetric --gap-outer on all four edges (matches the floating-card
       design spec). Note: PageCards rendered inside .content sit an extra
       16px in from this edge, since .content adds its own shadow-buffer
       padding below — so they don't line up pixel-for-pixel with the
       Navbar's edge. That's an acceptable, minor inset; making it exact
       would require giving Navbar a matching 16px buffer of its own,
       which isn't worth the added complexity since Navbar never scrolls
       and so never needs the buffer for shadow-clipping reasons. */
    padding: var(--gap-outer);
    gap: var(--gap-inner);
  }

  /* Navbar/Footer keep their own content-driven height (flex's default
     0 1 auto) and never move. This is the one scrollable region — capped to
     whatever's left of the viewport shell via min-height: 0, which overrides
     flex's default min-height: auto that would otherwise let it grow past
     that and push the footer down.
     padding: shadow buffer so overflow-y: auto doesn't clip PageCard
     box-shadows (Navbar has no equivalent buffer since it never scrolls). */
  .content {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
    padding: 16px 16px 24px;
  }
</style>
