<!--
  PostComposer
  Purpose: Input area for creating a new Post. Per CLAUDE.md, write access to the Forum is
    restricted to the Career age tier (16+) — this component should only ever be rendered for
    those users, but the create-post API call must also enforce this server-side.
  Used in: ForumFeed (rendered above the feed, career tier only)
  Props:
    - onSubmit ((body: string) => void): callback invoked with the composed text when the user
      submits. TODO: extend to support image/video attachments once media upload is designed.
  Behaviour:
    Textarea + submit button. Disable submit while body is empty/whitespace-only.
    Clear the textarea after a successful submit.
  Styling:
    Card base, textarea full-width with no resize handle, submit button (Button, primary)
    right-aligned below it.
-->
<script lang="ts">
  import Button from '$lib/components/Button.svelte';

  // The parent component passes a callback to handle the new post.
  export let onSubmit: (body: string) => void;

  let body = '';

  function handleSubmit() {
    const trimmedBody = body.trim();

    if (!trimmedBody) {
      return;
    }

    onSubmit(trimmedBody);
    body = '';
  }
</script>

<form class="composer" on:submit|preventDefault={handleSubmit}>
  <!-- Let the user type their post. -->
  <textarea
    bind:value={body}
    rows={4}
    placeholder="Write something..."
    class="textarea"
  />

  <!-- Submit the post when the text is not empty. -->
  <div class="actions">
    <Button type="submit" variant="primary" disabled={!body.trim()}>
      Post
    </Button>
  </div>
</form>

<style>
  .composer {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .textarea {
    width: 100%;
    resize: none;
    border: 1px solid #d1d5db;
    padding: 0.75rem;
    font: inherit;
    box-sizing: border-box;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }
</style>
