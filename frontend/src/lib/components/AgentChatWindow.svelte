<!--
  AgentChatWindow
  Purpose: Full conversation history view for the Dynamic Mentor (Amazon Bedrock, RAG, Socratic
    framework), as opposed to AgentChat which is just the input teaser shown in the CTASidebar.
  Used in: /library
  Props:
    - messages (Array<{ id: string; role: 'user' | 'mentor'; text: string; createdAt: string }>)
      TODO: replace with a real API type once the chat-history endpoint exists.
    - onSend ((text: string) => void): callback invoked when the user sends a new message.
  Behaviour:
    Render messages in order, user messages right-aligned, mentor messages left-aligned.
    Auto-scroll to the latest message when `messages` changes.
    Input field + send button pinned to the bottom.
    Per CLAUDE.md: this surface must not leak student telemetry outside the private VPC —
    that's a backend/API concern, not something this component needs to enforce, but keep it
    in mind if you add any client-side logging or analytics here.
  Styling:
    Full-height flex column: scrollable message list (flex-grow) + fixed input row at the
    bottom. Mentor messages use the orange-yellow accent as a left border or bubble tint.
-->
<script lang="ts">
  // Changes -------------
  import { tick } from "svelte";
  // Changes -------------
  interface ChatMessage {
    id: string;
    role: 'user' | 'mentor';
    text: string;
    createdAt: string;
  }

  export let messages: ChatMessage[];
  export let onSend: (text: string) => void;
  export let initialDraft: string = '';

  let draft = initialDraft;
  // Changes -------------
  let message_container: HTMLDivElement | undefined;
  
  
  $: if (messages) {
    // The conditional statement checks if the message variable exits or not null or undefined
    scroll_to_bottom();
  }
  // Auto-scroll whenever messages change
  
  async function scroll_to_bottom(){
    await tick();

    if (message_container) {
      message_container.scrollTop = message_container.scrollHeight;
    }
  }

  function send(){
    const text = draft.trim()

    if (!text) return
    // If the text is empty nothing is sent

    onSend(text);
    draft = ""
    // Sends a callback
  }
</script>

<div class="chat-window">

  <div class="messages" bind:this={message_container}>

    {#each messages as message (message.id)}
    <!-- Render messages in order -->
    <div
      class:user={message.role === "user"}
      class:mentor={message.role === "mentor"}
      class="message-row"
    > <!-- Assigns roles -->
      <div class="bubble">
        {message.text}
      </div>
    </div>

    {/each}
  </div>

  <div class="input-row">
    <input
      bind:value={draft}
      placeholder="Type a message..."
      on:keydown={(e) =>{
        if (e.key === "Enter") send();
      }}
    />

    <button on:click={send}>
      Send
    </button>
  </div>

</div>

<style>
  .chat-window {
	  height: 100%;
	  display: flex;
	  flex-direction: column;
  }

  .messages {
	  flex: 1;
	  overflow-y: auto;
	  padding: 1rem;
	  display: flex;
	  flex-direction: column;
	  gap: 0.75rem;
  }

  .message-row {
	  display: flex;
  }

  .user {
	  justify-content: flex-end;
  }

  .mentor {
	  justify-content: flex-start;
  }

  .bubble {
	  max-width: 75%;
	  padding: 0.75rem 1rem;
	  border-radius: 12px;
	  word-break: break-word;
  }

  .user .bubble {
	  background: #2563eb;
	  color: white;
  }

  .mentor .bubble {
	  background: #2d2d2d;
	  border-left: 4px solid orange;
	  color: white;
 }

  .input-row {
	  display: flex;
	  gap: 0.5rem;
	  padding: 1rem;
	  border-top: 1px solid #333;
 }

  .input-row input {
	  flex: 1;
	  padding: 0.75rem;
  }

  .input-row button {
	  padding: 0.75rem 1rem;
  }
</style>
<!-- Changes -------------------------->

<!-- TODO: Implement scrollable message list (auto-scrolling) + input row calling onSend(draft). -->
