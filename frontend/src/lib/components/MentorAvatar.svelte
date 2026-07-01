<!--
  MentorAvatar
  Purpose: The Dynamic Mentor's identity in the Discord-style chat message list
    (AgentChatWindow). A gradient circle whose hues are derived from the app's
    per-route palette system (gradient.ts) rather than a hardcoded colour, plus a
    slow "breathing" hue-shift so it reads as alive, not static.
  Used in: AgentChatWindow
  Props:
    - size (string): CSS size for width/height, default '38px' (in-chat size).
  Notes: A dot-matrix/lens-warp texture and a chromatic edge glow were both explored
    for this avatar during brainstorming and explicitly dropped — this is deliberately
    just the gradient + sheen highlights + breathe animation, nothing more.
-->
<script lang="ts">
  import { getShadowHues } from '$lib/gradient';

  export let size: string = '38px';

  const [hueA, hueB, hueC] = getShadowHues('/library');
</script>

<div
  class="mentor-avatar"
  style="width: {size}; height: {size}; --hue-a: {hueA}; --hue-b: {hueB}; --hue-c: {hueC};"
>
  <div class="core"></div>
  <div class="sheen"></div>
</div>

<style>
  .mentor-avatar {
    position: relative;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
  }

  .core {
    position: absolute;
    inset: -15%;
    background: radial-gradient(
      circle at 35% 30%,
      hsl(var(--hue-a) 85% 68%),
      hsl(var(--hue-b) 70% 55%) 55%,
      hsl(var(--hue-c) 60% 55%) 100%
    );
    animation: breathe 5s ease-in-out infinite alternate;
  }

  @keyframes breathe {
    0% {
      filter: hue-rotate(0deg) brightness(1);
    }
    100% {
      filter: hue-rotate(70deg) brightness(1.18);
    }
  }

  .sheen {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background:
      radial-gradient(circle at 40% 35%, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0) 45%),
      radial-gradient(circle at 65% 70%, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0) 50%);
  }

  @media (prefers-reduced-motion: reduce) {
    .core {
      animation: none;
    }
  }
</style>
