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

<a href="/dashboard">Dashboard</a>
{#each topics as topic}
  <a href="/topics/{topic.slug}">{topic.name}</a>
{/each}

<!-- TODO: Implement sidebar nav. Use <a href=...> links (SvelteKit handles client routing). -->
<!-- Apply active class when activePath starts with the link's href. -->
