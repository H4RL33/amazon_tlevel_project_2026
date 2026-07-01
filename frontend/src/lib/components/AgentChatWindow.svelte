<!--
  AgentChatWindow
  Purpose: Full conversation view for the Dynamic Mentor. Single-column, Discord-style
    message list (avatar + username + timestamp above each message, no left/right split
    between user and mentor), streaming-in text, and a coloured "send flourish" on the
    input row.
  Used in: /library (center column)
  Props:
    - messages (ChatMessageRecord[]): full message history for the active session.
    - onSend ((text: string) => void): called when the user submits a new message.
    - userDisplayName (string): current user's display name, shown above their messages.
    - streamingText (string | undefined): in-progress mentor reply text while a stream
      is active. When set (even to ''), an in-progress mentor message row renders with
      this text, using the per-chunk blur-in span treatment.
    - isStreaming (boolean): drives the chat card's inner chromatic glow.
-->
<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { blur } from 'svelte/transition';
  import MentorAvatar from '$lib/components/MentorAvatar.svelte';
  import type { ChatMessageRecord } from '$lib/api/chat';

  export let messages: ChatMessageRecord[];
  export let onSend: (text: string) => void;
  export let userDisplayName: string;
  export let streamingText: string | undefined = undefined;
  export let isStreaming: boolean = false;

  let draft = '';
  let messageContainer: HTMLDivElement | undefined;
  let flourish = false;

  // svelte/transition's `blur` doesn't respect prefers-reduced-motion itself,
  // so we zero out the duration when the user has requested reduced motion
  // (same convention as +layout.svelte's pageFadeDuration).
  let chunkBlurDuration = 700;

  $: if (messages || streamingText) {
    scrollToBottom();
  }

  async function scrollToBottom() {
    await tick();
    if (messageContainer) {
      messageContainer.scrollTop = messageContainer.scrollHeight;
    }
  }

  function formatTime(iso: string): string {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function send() {
    const text = draft.trim();
    if (!text) return;
    onSend(text);
    draft = '';
    flourish = false;
    void tick().then(() => (flourish = true));
  }

  onMount(() => {
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    chunkBlurDuration = reducedMotionQuery.matches ? 0 : 700;
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      chunkBlurDuration = e.matches ? 0 : 700;
    };
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange);
    return () => reducedMotionQuery.removeEventListener('change', handleReducedMotionChange);
  });
</script>

<div class="chat-window" class:streaming={isStreaming}>
  <div class="messages" bind:this={messageContainer}>
    {#each messages as message (message.id)}
      <div class="message-row">
        {#if message.role === 'mentor'}
          <MentorAvatar />
        {:else}
          <div class="user-avatar">{userDisplayName.slice(0, 2).toUpperCase()}</div>
        {/if}
        <div class="message-body">
          <div class="message-head">
            <span class="message-name"
              >{message.role === 'mentor' ? 'Dynamic Mentor' : userDisplayName}</span
            >
            <span class="message-time">{formatTime(message.created_at)}</span>
          </div>
          <p class="message-text">{message.text}</p>
          {#if message.sources && message.sources.length > 0}
            <div class="sources">
              {#each message.sources as source (source.content_id)}
                <span class="source-chip">{source.title}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {/each}

    {#if streamingText !== undefined}
      <div class="message-row">
        <MentorAvatar />
        <div class="message-body">
          <div class="message-head">
            <span class="message-name">Dynamic Mentor</span>
          </div>
          <p class="message-text">
            {#each streamingText.split(' ') as word, i (i)}<span
                class="chunk"
                in:blur={{ duration: chunkBlurDuration, amount: 6 }}>{word} </span
              >{/each}
          </p>
        </div>
      </div>
    {/if}
  </div>

  <form class="input-row" class:flourish on:submit|preventDefault={send}>
    <input
      bind:value={draft}
      type="text"
      placeholder="Ask your mentor anything..."
      autocomplete="off"
    />
    <button type="submit" aria-label="Send">Send</button>
  </form>
</div>

<style>
  .chat-window {
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  /* Streaming glow: large four-hue inset glow layered on the card's own edges,
     colour-cycling continuously while active, with a fog-like blur+opacity
     creep-in/dissipate rather than a plain fade. Lives on ::before so it
     composes with PageCard's own outer drop-shadow instead of replacing it. */
  .chat-window::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0;
    filter: blur(22px);
    transition:
      opacity 1.1s ease-in,
      filter 1.1s ease-in;
    animation: glow-cycle 6s linear infinite;
    pointer-events: none;
  }

  .chat-window.streaming::before {
    opacity: 1;
    filter: blur(0px);
    transition:
      opacity 0.9s ease-out,
      filter 0.9s ease-out;
  }

  @keyframes glow-cycle {
    0%,
    100% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(20 75% 60% / 0.55),
        inset -40px 40px 90px -20px hsl(130 70% 55% / 0.5),
        inset -40px -40px 90px -20px hsl(240 65% 58% / 0.5),
        inset 40px -40px 90px -20px hsl(310 70% 60% / 0.5);
    }
    33% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(150 75% 55% / 0.55),
        inset -40px 40px 90px -20px hsl(260 70% 58% / 0.5),
        inset -40px -40px 90px -20px hsl(10 65% 60% / 0.5),
        inset 40px -40px 90px -20px hsl(80 70% 55% / 0.5);
    }
    66% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(280 75% 58% / 0.55),
        inset -40px 40px 90px -20px hsl(30 70% 60% / 0.5),
        inset -40px -40px 90px -20px hsl(100 65% 55% / 0.5),
        inset 40px -40px 90px -20px hsl(210 70% 58% / 0.5);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .chat-window::before {
      animation: none;
      transition: opacity 0.3s ease;
    }
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 0.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }

  .message-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .user-avatar {
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    border-radius: 50%;
    background: #232f3e;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-body {
    flex: 1;
    min-width: 0;
  }

  .message-head {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.15rem;
  }

  .message-name {
    font-weight: 700;
    font-size: 0.85rem;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-time {
    font-size: 0.7rem;
    color: #8a94a3;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-text {
    font-size: 0.875rem;
    line-height: 1.6;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
    margin: 0;
    word-break: break-word;
  }

  .chunk {
    display: inline-block;
  }

  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.5rem;
  }

  .source-chip {
    font-size: 0.7rem;
    background: rgba(35, 47, 62, 0.08);
    color: #232f3e;
    border-radius: 99px;
    padding: 0.15rem 0.5rem;
    font-weight: 500;
    font-family: 'Ubuntu', sans-serif;
  }

  .input-row {
    display: flex;
    align-items: center;
    background: white;
    border-bottom: 3px solid transparent;
    border-image: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700)) 1;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    margin-top: 1rem;
    flex-shrink: 0;
    position: relative;
  }

  .input-row.flourish {
    animation: flourish-glow 0.55s ease-out;
  }

  .input-row.flourish::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -3px;
    height: 3px;
    animation: flourish-spin 0.55s ease-out;
  }

  @keyframes flourish-spin {
    0% {
      background: linear-gradient(to right, hsl(0 55% 58%), hsl(60 55% 58%));
    }
    25% {
      background: linear-gradient(to right, hsl(90 55% 55%), hsl(160 55% 52%));
    }
    50% {
      background: linear-gradient(to right, hsl(190 50% 52%), hsl(230 50% 55%));
    }
    75% {
      background: linear-gradient(to right, hsl(280 50% 58%), hsl(320 50% 58%));
    }
    100% {
      background: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700));
    }
  }

  @keyframes flourish-glow {
    0% {
      box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
    40% {
      box-shadow:
        0 10px 20px -4px hsl(300 45% 60% / 0.25),
        0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
    100% {
      box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .input-row.flourish {
      animation: none;
    }
    .input-row.flourish::after {
      animation: none;
    }
  }

  .input-row input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.875rem 1rem;
    font-size: 0.95rem;
    background: transparent;
    color: black;
    font-family: 'Ubuntu', sans-serif;
  }

  .input-row button {
    border: none;
    background: transparent;
    padding: 0 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-family: 'Ubuntu', sans-serif;
    color: #232f3e;
  }
</style>
