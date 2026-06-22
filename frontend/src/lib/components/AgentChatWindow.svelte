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
  interface ChatMessage {
    id: string;
    role: 'user' | 'mentor';
    text: string;
    createdAt: string;
  }

  export let messages: ChatMessage[];
  export let onSend: (text: string) => void;

  let draft = '';
</script>

<!-- TODO: Implement scrollable message list (auto-scrolling) + input row calling onSend(draft). -->
