<!--
  Card
  Purpose: Surface container for grouped content.
  Used in: Dashboard panels, topic cards, T-level list items, content blocks.
  Props:
    - title (string | undefined): optional heading rendered above the default slot
  Slots:
    - default: main card body content
    - actions: optional footer row for action buttons (right-aligned)
  Styling:
    background #161b22, border-radius 8px, padding 1.5rem,
    box-shadow 0 1px 4px rgba(0,0,0,0.3), border 1px solid #21262d
-->

<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
<!-- Changes ----------------------------------->

<script lang="ts">

  // Optional card title.
  // If no title is provided, the heading is not rendered.
  export let title: string | undefined = undefined;

</script>

<!-- Main card container -->
<div class="card">
  <!-- Only render the heading if a title exists -->
  {#if title}
    <h2 class="card-title">{title}</h2>
  {/if}

  <!-- Default slot for the main card content -->
  <div class="card-body">
    <slot />
  </div>

   <!--
    Named slot for actions such as buttons.
    If nothing is placed in the "actions" slot,
    this section simply renders nothing.
  -->
  
  <div class="card-actions">
    <slot name="actions" />
  </div>
</div>

<style>
  /* Main card styling */
  .card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  }

  /* Optional title */
  .card-title {
    margin: 0 0 1rem;
    font-size: 1.25rem;
    font-weight: 600;
  }

  /* Main content area */
  .card-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Footer actions aligned to the right */
  .card-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }
</style>

<!-- TODO: Implement card template with optional title, default slot, and actions slot -->
<!-- Changes ----------------------------------->
<!-- Code may contain bugs or may be unfinished, most likely needs to be updated -------->
