# Shell & Layout Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the originally-planned `AppShell`/route-group split with a single shared layout for every route, move global navigation (Library/Dashboard links, login state, avatar dropdown) into `Navbar`, narrow `NavSidebar` to a page-scoped topic list, and fill in `HelpPanel` and a `/login` placeholder — per `docs/superpowers/specs/2026-06-24-shell-layout-design.md`.

**Architecture:** No new layout files. `Navbar.svelte` (already used by the existing root `+layout.svelte`) gains a `Library` link and a right-aligned auth slot (`NavBarAvatar` or a "Log in" `NavLink`) driven by the existing `currentUser` store. `NavSidebar.svelte` loses its `user` prop and global-nav markup, keeping only the topic-list section-nav role. `AppShell.svelte` is deleted outright since nothing ever imports it.

**Tech Stack:** SvelteKit + TypeScript, Vite, Vitest, Histoire (component previews), Prettier + ESLint.

---

### Task 1: Delete `AppShell.svelte`

`AppShell` was scaffolded for the route-group split the spec rejects (see "Architecture" in the design doc) and is never imported by any route. Removing it now, first, means no later task in this plan can accidentally depend on it.

**Files:**
- Delete: `frontend/src/lib/components/AppShell.svelte`
- Create: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing regression test**

Create `frontend/src/lib/shell.test.ts`:

```ts
import { existsSync } from 'node:fs';
import { describe, it, expect } from 'vitest';

describe('AppShell removal', () => {
  it('AppShell.svelte no longer exists', () => {
    expect(existsSync('src/lib/components/AppShell.svelte')).toBe(false);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: `shell.test.ts` FAILS — `AppShell.svelte` still exists at this point.

- [ ] **Step 3: Delete the file**

Run: `rm frontend/src/lib/components/AppShell.svelte` (from repo root)

- [ ] **Step 4: Run the test again to verify it passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green, including the pre-existing `scaffold.test.ts` suite.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/AppShell.svelte frontend/src/lib/shell.test.ts
git commit -m "refactor: delete AppShell.svelte, superseded by single shared layout"
```

---

### Task 2: Narrow `NavSidebar`'s prop contract

`NavSidebar` is currently a global app sidebar (topic links, a Dashboard link, user info, a Settings link). Per the design spec, it becomes a page-scoped topic-list section nav only — global nav moves to `Navbar`/`NavBarAvatar` in Task 4.

**Files:**
- Modify: `frontend/src/lib/components/NavSidebar.svelte`
- Modify: `frontend/src/lib/components/NavSidebar.story.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('NavSidebar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavSidebar.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — this test doesn't yet exercise the new prop contract; it's here to
catch a compile break in the next step before it ships.

- [ ] **Step 3: Replace `NavSidebar.svelte`'s contents**

```svelte
<!--
  NavSidebar
  Purpose: Topic-list section nav, used inline within pages that need to browse by
    Topic (e.g. /topics, /learn) -- not a persistent global app sidebar. Global nav
    (Library/Dashboard/avatar) lives in Navbar/NavBarAvatar instead.
  Used in: /topics, /learn (wired up in a later chapter)
  Props:
    - topics (TopicResponse[]): list of all 5 topics to render as nav links
    - activePath (string): current URL path -- highlight matching topic link
  Layout:
    Topic links -> /topics/[slug] for each topic.
  Styling:
    background #0a2540, full height, width 240px, padding 1rem 0.75rem,
    text-primary #c9d1d9, text-muted #8b949e, font-size 0.875rem
    Active link: bold, accent_colour left border, background rgba(31,111,235,0.1)
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';

  export let topics: TopicResponse[];
  export let activePath: string;
</script>

<nav class="sidebar">
  {#each topics as topic}
    <a href={`/topics/${topic.slug}`} class:active={activePath.startsWith(`/topics/${topic.slug}`)}>
      {topic.name}
    </a>
  {/each}
</nav>

<style>
  .sidebar {
    background: #0a2540;
    height: 100%;
    width: 240px;
    padding: 1rem 0.75rem;
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
</style>
```

- [ ] **Step 4: Update `NavSidebar.story.svelte` to match the new props**

Read the current file first (`frontend/src/lib/components/NavSidebar.story.svelte`) —
it currently passes a `user` prop that no longer exists. Replace its contents:

```svelte
<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { TopicResponse } from '$lib/api/types';
  import NavSidebar from './NavSidebar.svelte';

  export let Hst: Hst;

  const topics: TopicResponse[] = [
    {
      id: 1,
      slug: 'cloud-computing',
      name: 'Cloud Computing',
      description: '',
      accent_colour: '#1f6feb',
    },
    {
      id: 2,
      slug: 'digital-production',
      name: 'Digital Production',
      description: '',
      accent_colour: '#ff9900',
    },
  ];
</script>

<Hst.Story title="NavSidebar">
  <Hst.Variant title="Default">
    <div style="height: 500px;">
      <NavSidebar {topics} activePath="/topics/cloud-computing" />
    </div>
  </Hst.Variant>
</Hst.Story>
```

- [ ] **Step 5: Run the test suite and Histoire build to verify everything still compiles**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

Run (from `frontend/`): `npm run story:build`
Expected: `✅ Built N stories` with no errors (N is whatever the current total is —
this step is a compile check, not a count check).

- [ ] **Step 6: Format and commit**

```bash
cd frontend && npx prettier --write src/lib/components/NavSidebar.svelte src/lib/components/NavSidebar.story.svelte src/lib/shell.test.ts && cd ..
git add frontend/src/lib/components/NavSidebar.svelte frontend/src/lib/components/NavSidebar.story.svelte frontend/src/lib/shell.test.ts
git commit -m "refactor: narrow NavSidebar to a page-scoped topic-list nav"
```

---

### Task 3: Implement `NavBarAvatar.svelte`

`UserResponse` (in `frontend/src/lib/api/types.ts`) has no avatar-image field yet (avatar/header-image columns don't exist on the backend `User` model until the backend User Profiles chapter lands), so this implements the initials-only path — there's no data source for an image today.

**Files:**
- Modify: `frontend/src/lib/components/NavBarAvatar.svelte`
- Create: `frontend/src/lib/components/NavBarAvatar.story.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('NavBarAvatar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavBarAvatar.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — `NavBarAvatar.svelte` already exists as a stub with a valid default
export; this confirms the baseline before the rewrite.

- [ ] **Step 3: Replace `NavBarAvatar.svelte`'s contents**

```svelte
<!--
  NavBarAvatar
  Purpose: User avatar shown on the right of the NavBar with a dropdown for the
    user's Dashboard, Settings, and Help.
  Used in: NavBar
  Props:
    - user (UserResponse): current user -- renders initials from first_name/
      last_name on a coloured circle. (UserResponse has no avatar-image field yet;
      once one exists, this can branch to an <img> instead.)
  Behaviour:
    - Clicking the avatar toggles a dropdown panel anchored below-right of the avatar.
    - Dropdown items: "Dashboard" (/dashboard), "Settings" (/settings), "Help" (/help).
    - Clicking outside the dropdown or pressing Escape closes it.
  Styling:
    Avatar: 36px circle.
    Dropdown: background #161b22, border 1px solid #21262d, border-radius 8px,
    box-shadow 0 4px 12px rgba(0,0,0,0.4), min-width 180px.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

  export let user: UserResponse;

  let open = false;
  let containerEl: HTMLDivElement;

  function toggle() {
    open = !open;
  }

  function close() {
    open = false;
  }

  function handleWindowClick(event: MouseEvent) {
    if (open && containerEl && !containerEl.contains(event.target as Node)) {
      close();
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (open && event.key === 'Escape') {
      close();
    }
  }

  $: initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();
</script>

<svelte:window on:click={handleWindowClick} on:keydown={handleKeydown} />

<div class="avatar-container" bind:this={containerEl}>
  <button class="avatar-button" on:click={toggle} aria-haspopup="true" aria-expanded={open}>
    <span class="avatar">{initials}</span>
  </button>

  {#if open}
    <div class="dropdown" role="menu">
      <a href="/dashboard" role="menuitem">Dashboard</a>
      <a href="/settings" role="menuitem">Settings</a>
      <a href="/help" role="menuitem">Help</a>
    </div>
  {/if}
</div>

<style>
  .avatar-container {
    position: relative;
  }

  .avatar-button {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }

  .avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #1f6feb;
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 700;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    min-width: 180px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
    z-index: 10;
  }

  .dropdown a {
    color: #c9d1d9;
    text-decoration: none;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .dropdown a:hover {
    background: rgba(255, 255, 255, 0.05);
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Add `NavBarAvatar.story.svelte`**

```svelte
<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { UserResponse } from '$lib/api/types';
  import NavBarAvatar from './NavBarAvatar.svelte';

  export let Hst: Hst;

  const user: UserResponse = {
    id: 1,
    cognito_sub: 'sub-1',
    email: 'jordan@example.com',
    first_name: 'Jordan',
    last_name: 'Smith',
    created_at: new Date().toISOString(),
  };
</script>

<Hst.Story title="NavBarAvatar">
  <Hst.Variant title="Default">
    <div style="background: #232f3e; padding: 1rem; display: flex; justify-content: flex-end;">
      <NavBarAvatar {user} />
    </div>
  </Hst.Variant>
</Hst.Story>
```

- [ ] **Step 6: Run the Histoire build to verify it compiles**

Run (from `frontend/`): `npm run story:build`
Expected: `✅ Built N stories` with no errors, one more story than before this task.

- [ ] **Step 7: Format and commit**

```bash
cd frontend && npx prettier --write src/lib/components/NavBarAvatar.svelte src/lib/components/NavBarAvatar.story.svelte src/lib/shell.test.ts && cd ..
git add frontend/src/lib/components/NavBarAvatar.svelte frontend/src/lib/components/NavBarAvatar.story.svelte frontend/src/lib/shell.test.ts
git commit -m "feat: implement NavBarAvatar dropdown"
```

---

### Task 4: Wire `Library`, auth-aware links, and the avatar/login slot into `Navbar`

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`
- Modify: `frontend/src/lib/components/Navbar.story.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('Navbar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — `Navbar.svelte` already exports a default component; this is the
baseline before the rewrite.

- [ ] **Step 3: Replace `Navbar.svelte`'s contents**

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import NavBarAvatar from '$lib/components/NavBarAvatar.svelte';
  import { currentUser } from '$lib/stores/user';
</script>

<nav>
  <a href="/" class="logo-link">
    <img src="/assets/logo.png" alt="T Level Placements at Amazon" class="logo" />
  </a>
  <div class="links">
    <NavLink href="/" label="Home" />
    <NavLink href="/learn" label="Learn" />
    <NavLink href="/topics" label="Topics" />
    <NavLink href={$currentUser ? '/library' : '/login'} label="Library" />
    <NavLink href={$currentUser ? '/dashboard' : '/login'} label="Dashboard" />
    {#if $currentUser}
      <NavBarAvatar user={$currentUser} />
    {:else}
      <NavLink href="/login" label="Log in" />
    {/if}
  </div>
</nav>

<style>
  nav {
    display: flex;
    align-items: center;
    background: #232f3e;
    padding: 0 1.5rem;
    height: 64px;
    width: 100%;
    box-sizing: border-box;
  }

  .logo-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    flex-shrink: 0;
  }

  .logo {
    height: 40px;
  }

  .links {
    margin-left: auto;
    display: flex;
    gap: 1.5rem;
    align-items: center;
    overflow: visible;
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Update `Navbar.story.svelte`**

Read the current file first (`frontend/src/lib/components/Navbar.story.svelte`).
Replace its contents. `currentUser` is a module-level singleton store, so setting it
in this file's script affects every variant rendered from it — there is no per-
variant isolation. Rather than relying on uncertain lifecycle hooks to set it only
for "one" variant, this story sets it once at the top level and shows the logged-in
(avatar) state, which is the more complex path worth previewing; the logged-out
"Log in" link's appearance is already covered by `NavLink.story.svelte`:

```svelte
<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import type { UserResponse } from '$lib/api/types';
  import Navbar from './Navbar.svelte';
  import { currentUser } from '$lib/stores/user';

  export let Hst: Hst;

  const user: UserResponse = {
    id: 1,
    cognito_sub: 'sub-1',
    email: 'jordan@example.com',
    first_name: 'Jordan',
    last_name: 'Smith',
    created_at: new Date().toISOString(),
  };

  currentUser.set(user);
</script>

<Hst.Story title="Navbar">
  <Hst.Variant title="Logged in">
    <Navbar />
  </Hst.Variant>
</Hst.Story>
```

- [ ] **Step 6: Run the Histoire build to verify it compiles**

Run (from `frontend/`): `npm run story:build`
Expected: `✅ Built N stories` with no errors.

- [ ] **Step 7: Format and commit**

```bash
cd frontend && npx prettier --write src/lib/components/Navbar.svelte src/lib/components/Navbar.story.svelte src/lib/shell.test.ts && cd ..
git add frontend/src/lib/components/Navbar.svelte frontend/src/lib/components/Navbar.story.svelte frontend/src/lib/shell.test.ts
git commit -m "feat: add Library link and auth-aware avatar/login slot to Navbar"
```

---

### Task 5: Implement `HelpPanel.svelte`

**Files:**
- Modify: `frontend/src/lib/components/HelpPanel.svelte`
- Create: `frontend/src/lib/components/HelpPanel.story.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('HelpPanel', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/HelpPanel.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — baseline check before the rewrite.

- [ ] **Step 3: Replace `HelpPanel.svelte`'s contents**

```svelte
<!--
  HelpPanel
  Purpose: Content panel for the "Help" destination reachable from the NavBarAvatar
    dropdown.
  Used in: /help
  Props: none -- static FAQ list, hardcoded for now.
  Styling:
    Card base, simple FAQ-style layout (question as heading, answer as body text
    below it).
-->
<script lang="ts">
  const faqs: Array<{ question: string; answer: string }> = [
    {
      question: 'What is a Snippet?',
      answer:
        'A Snippet is a single short-form piece of content — an article, audio clip, or video — that you can read or watch without needing an account.',
    },
    {
      question: 'What is an Album?',
      answer:
        'An Album is a curated set of Snippets forming a learning pathway, like "Cloud Computing T-Level". Enrolling in an Album requires an account so we can track your progress.',
    },
    {
      question: 'Do I need an account to use Living Campus?',
      answer:
        'No — Snippets and Albums are publicly browsable. An account lets you enrol in Albums, track your progress, save Snippets to your Library, and use the social Forum (age permitting).',
    },
  ];
</script>

<div class="help-panel">
  {#each faqs as faq}
    <div class="faq-item">
      <h3>{faq.question}</h3>
      <p>{faq.answer}</p>
    </div>
  {/each}
</div>

<style>
  .help-panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 700px;
    margin: 0 auto;
  }

  .faq-item {
    margin-bottom: 1.5rem;
  }

  .faq-item:last-child {
    margin-bottom: 0;
  }

  .faq-item h3 {
    color: #c9d1d9;
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }

  .faq-item p {
    color: #8b949e;
    font-size: 0.875rem;
    line-height: 1.6;
    margin: 0;
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Add `HelpPanel.story.svelte`**

```svelte
<script lang="ts">
  import type { Hst } from '@histoire/plugin-svelte';
  import HelpPanel from './HelpPanel.svelte';

  export let Hst: Hst;
</script>

<Hst.Story title="HelpPanel">
  <Hst.Variant title="Default">
    <HelpPanel />
  </Hst.Variant>
</Hst.Story>
```

- [ ] **Step 6: Run the Histoire build to verify it compiles**

Run (from `frontend/`): `npm run story:build`
Expected: `✅ Built N stories` with no errors, one more story than before this task.

- [ ] **Step 7: Format and commit**

```bash
cd frontend && npx prettier --write src/lib/components/HelpPanel.svelte src/lib/components/HelpPanel.story.svelte src/lib/shell.test.ts && cd ..
git add frontend/src/lib/components/HelpPanel.svelte frontend/src/lib/components/HelpPanel.story.svelte frontend/src/lib/shell.test.ts
git commit -m "feat: implement HelpPanel with a static FAQ list"
```

---

### Task 6: Wire `/help` to render `HelpPanel`

**Files:**
- Modify: `frontend/src/routes/help/+page.svelte`

- [ ] **Step 1: Replace the placeholder page**

Current contents of `frontend/src/routes/help/+page.svelte` (the "Coming soon"
placeholder from the skeleton chapter) — replace entirely with:

```svelte
<script lang="ts">
  import HelpPanel from '$lib/components/HelpPanel.svelte';
</script>

<main>
  <h1>Help</h1>
  <HelpPanel />
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 2: Run the full test suite to verify nothing broke**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 3: Format and commit**

```bash
cd frontend && npx prettier --write src/routes/help/+page.svelte && cd ..
git add frontend/src/routes/help/+page.svelte
git commit -m "feat: render HelpPanel on the /help route"
```

---

### Task 7: Create the `/login` placeholder route

**Files:**
- Create: `frontend/src/routes/login/+page.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('/login page', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('../routes/login/+page.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: FAIL — `frontend/src/routes/login/+page.svelte` doesn't exist yet.

- [ ] **Step 3: Create `frontend/src/routes/login/+page.svelte`**

```svelte
<main>
  <h1>Sign in</h1>
  <p>Sign-in is coming soon. In the meantime, you can keep browsing Snippets, Albums, and Topics without an account.</p>
  <a href="/">Back to Home</a>
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }

  a {
    color: #1f6feb;
  }
</style>
```

- [ ] **Step 4: Run the test again to verify it passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 5: Format and commit**

```bash
cd frontend && npx prettier --write src/routes/login/+page.svelte src/lib/shell.test.ts && cd ..
git add frontend/src/routes/login/+page.svelte frontend/src/lib/shell.test.ts
git commit -m "feat: add /login placeholder route"
```

---

### Task 8: Full local verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full frontend test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: all tests PASS, including the pre-existing `scaffold.test.ts` suite and
every test added in this plan's `shell.test.ts`.

- [ ] **Step 2: Run lint**

Run (from `frontend/`): `npm run lint`
Expected: no errors. If Prettier flags formatting issues in files this plan touched,
run `npm run format` and re-check; do not fix pre-existing formatting issues in
unrelated files as part of this plan.

- [ ] **Step 3: Run the SvelteKit type checker**

Run (from `frontend/`): `npm run check`
Expected: no errors. This catches any leftover prop-type mismatches (e.g. anything
still passing a `user` prop to the narrowed `NavSidebar`).

- [ ] **Step 4: Run the full Histoire build**

Run (from `frontend/`): `npm run story:build`
Expected: all stories build with no errors — confirms `NavBarAvatar.story.svelte`,
`HelpPanel.story.svelte`, the updated `Navbar.story.svelte`, and the updated
`NavSidebar.story.svelte` all compile together cleanly.

- [ ] **Step 5: Manually verify in the running app**

Run (from `frontend/`): `npm run dev`, open `http://localhost:5173` (or whatever
port Vite reports).
Verify:
- The Navbar shows Home/Learn/Topics/Library/Dashboard plus a "Log in" link on the
  far right (since no auth exists yet, `currentUser` is always `null` at this point).
- Clicking "Log in" navigates to `/login` and shows the placeholder page.
- Clicking "Library" or "Dashboard" also navigates to `/login` (since `$currentUser`
  is `null`).
- `/help` renders the FAQ list from `HelpPanel`.
