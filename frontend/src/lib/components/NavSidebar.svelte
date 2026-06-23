<!--
  NavSidebar
  Purpose: Persistent left navigation showing topic links, branding, user info, and settings.
  Used in: AppShell
  Props:
    - user (UserResponse | null): current user — show first_name or "Guest" if null
    - topics (TopicResponse[]): list of all 5 topics to render as nav links
    - activePath (string): current URL path — highlight matching topic link
  Layout (top to bottom):
    1. Branding: "AWS Academy" logo text
    2. Divider
    3. "Dashboard" link → /dashboard
    4. Topic links → /topics/[slug] for each topic.
       Each link has a 3px left border in the topic's accent_colour on hover/active.
    5. Spacer (flex-grow)
    6. User name + email in small text
    7. Settings link → /settings (gear icon or "Settings" text)
  Styling:
    background #0a2540, full height, width 240px, padding 1rem 0.75rem,
    text-primary #c9d1d9, text-muted #8b949e, font-size 0.875rem
    Active link: bold, accent_colour left border, background rgba(31,111,235,0.1)
-->
<script lang="ts">
  import type { TopicResponse, UserResponse } from '$lib/api/types';

  export let user: UserResponse | null;
  export let topics: TopicResponse[];
  export let activePath: string;


</script>

<!-- Changes -->

<nav class="sidebar">
  <div class="branding">AWS Academy</div>
  <!-- Code above displays the logo text-->
  <hr />
  <a href="/dashboard" class:active={activePath === '/dashboard'}>Dashboard</a>
  {#each topics as topic}
    <a href={`/topics/${topic.slug}`} class:active={activePath.startsWith(`/topics/${topic.slug}`)}>
      {topic.name}
    </a>
  <!-- Code above displays the topics link -->
  {/each}
  <div class="spacer"></div>
  <div class="user-info">
    <div>{user ? user.first_name : 'Guest'}</div>
    <!-- Code above displays the user's first name or "Guest" if there is no user -->
    {#if user}
      <div class="email">{user.email}</div>
    {/if}

  </div>
  <a href="/settings" class:active={activePath === '/settings'}>Settings</a>
</nav>
<style>
  .sidebar {
    background: #0a2540;
    height: 100%;
    width: 240px;
    padding: 1rem 0.75rem;
  }

  .branding {
    color: #c9d1d9;
    font-size: 1.25rem;
    font-weight: bold;
    margin-bottom: 1rem;
  }

  hr {
    border: none;
    border-top: 1px solid #3a3a3a;
    margin: 1rem 0;
  }

  a {
    color: #c9d1d9;
    text-decoration: none;
    font-size: 0.875rem;
    padding: 0.5rem 0;
    display: block;
  }

  a:hover,
  a.active {
    background-color: rgba(31, 111, 235, 0.1);
    border-left: 3px solid #1f6ffb;
    font-weight: bold;
  }

  .spacer {
    flex-grow: 1;
  }

  .user-info {
    margin-top: auto;
    margin-bottom: 1rem;
  }

  .email {
    color: #8b949e;
    font-size: 0.75rem;
  }
</style>

<!-- Changes -->

<!-- TODO: Implement sidebar nav. Use <a href=...> links (SvelteKit handles client routing). -->
<!-- Apply active class when activePath starts with the link's href. -->
