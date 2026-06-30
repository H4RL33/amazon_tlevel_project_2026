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
  export let onSubmit: (body: string) => void;

  let body = '';
</script>

<!-- TODO: Implement textarea + submit button, calling onSubmit(body) and clearing body after. -->
