/**
 * Svelte action: subtle 3D tilt that follows the cursor, GPU-cheap by design.
 *
 * Deliberately event-driven, not a continuous animation loop — the perf work
 * elsewhere this session measured a ~5x frame-rate regression from combining
 * an animated `filter` with a continuously-running `transform`. This action
 * only writes a `transform` (translateZ/rotateX/rotateY — all compositor-only,
 * no repaint) in response to real pointermove events, batched to one write per
 * animation frame via requestAnimationFrame, and does nothing at all while the
 * pointer isn't moving. No `filter` is touched here.
 */
export interface TiltOptions {
  /** Max rotation in degrees at the card's edge. Keep small — this should read as a hint of depth, not a gimmick. */
  maxTilt?: number;
}

export function tilt(node: HTMLElement, options: TiltOptions = {}) {
  const maxTilt = options.maxTilt ?? 8;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReducedMotion) {
    return {};
  }

  let rafId: number | null = null;
  let pendingX = 0;
  let pendingY = 0;

  function applyTilt() {
    rafId = null;
    node.style.transform = `perspective(600px) rotateX(${pendingY}deg) rotateY(${pendingX}deg) scale3d(1.03, 1.03, 1.03)`;
  }

  function handlePointerMove(e: PointerEvent) {
    const rect = node.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    pendingX = px * maxTilt * 2;
    pendingY = -py * maxTilt * 2;
    if (rafId === null) {
      rafId = requestAnimationFrame(applyTilt);
    }
  }

  function handlePointerLeave() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    node.style.transition = 'transform 0.4s ease';
    node.style.transform = '';
    const clearTransition = () => {
      node.style.transition = '';
      node.removeEventListener('transitionend', clearTransition);
    };
    node.addEventListener('transitionend', clearTransition);
  }

  function handlePointerEnter() {
    // Ease the initial engagement (identity -> first tilted/scaled transform)
    // so the scale-up doesn't snap in — then drop the transition once that's
    // done so live cursor-tracking on pointermove stays lag-free.
    node.style.transition = 'transform 0.2s ease-out';
    const clearEngageTransition = () => {
      node.style.transition = 'none';
      node.removeEventListener('transitionend', clearEngageTransition);
    };
    node.addEventListener('transitionend', clearEngageTransition);
  }

  node.addEventListener('pointerenter', handlePointerEnter);
  node.addEventListener('pointermove', handlePointerMove);
  node.addEventListener('pointerleave', handlePointerLeave);

  return {
    destroy() {
      if (rafId !== null) cancelAnimationFrame(rafId);
      node.removeEventListener('pointerenter', handlePointerEnter);
      node.removeEventListener('pointermove', handlePointerMove);
      node.removeEventListener('pointerleave', handlePointerLeave);
    },
  };
}
