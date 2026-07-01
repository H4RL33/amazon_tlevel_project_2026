# Settings UI Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Button component, extract an AvatarBadge, restyle the NavBarAvatar dropdown to match the white-card design system, and redesign the Settings page with a sidebar layout and client-side image processing.

**Architecture:** Four independent frontend files change. AvatarBadge is extracted first (no deps), Button is rewritten in parallel (no deps), then NavBarAvatar consumes AvatarBadge, and finally the Settings page consumes both. No backend changes. No new API calls.

**Tech Stack:** SvelteKit, TypeScript, Canvas API (processImage), vitest (image processing unit test).

**Spec:** `docs/superpowers/specs/2026-06-26-settings-ui-polish-design.md`

---

## File Map

| File | Status | Responsibility |
|------|--------|----------------|
| `frontend/src/lib/components/Button.svelte` | Rewrite | Generic button with variant/disabled/type props and slot |
| `frontend/src/lib/components/AvatarBadge.svelte` | Create | Renders initials circle or avatar image at a given size |
| `frontend/src/lib/components/NavBarAvatar.svelte` | Modify | Uses AvatarBadge; white-card dropdown with NavLink items |
| `frontend/src/routes/settings/+page.svelte` | Rewrite | Sidebar + content layout; image processing pipeline |

---

### Task 1: Rewrite Button.svelte

**Files:**
- Rewrite: `frontend/src/lib/components/Button.svelte`

The current file is a broken stub (two `<script>` blocks, hardcoded `onclick=alert()`, renders all three variants at once). Replace it entirely.

- [ ] **Step 1: Replace the full file contents**

Write `frontend/src/lib/components/Button.svelte`:

```svelte
<!--
  Button
  Purpose: Standard interactive button with variant styles.
  Used in: All pages — forms, CTAs, actions.
  Props:
    - variant ('primary' | 'secondary' | 'danger'): visual style.
      primary = AWS blue (#1f6feb), secondary = muted surface (#21262d), danger = red (#ef4444)
    - disabled (boolean): disables interaction, reduces opacity to 0.5
    - type ('button' | 'submit' | 'reset'): HTML button type, default 'button'
  Slots: default — button label text or content
  Events: forwards native 'click' event to parent
  Styling: border-radius 6px, padding 0.5rem 1.25rem, font-size 0.875rem, cursor pointer
-->
<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'danger' = 'primary';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
</script>

<button
  {type}
  {disabled}
  class={variant}
  on:click
>
  <slot />
</button>

<style>
  button {
    font-family: 'Ubuntu', sans-serif;
    border-radius: 6px;
    padding: 0.5rem 1.25rem;
    font-size: 0.875rem;
    cursor: pointer;
    border: none;
    color: #ffffff;
    transition: opacity 0.15s;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .primary {
    background: #1f6feb;
  }

  .secondary {
    background: #21262d;
  }

  .danger {
    background: #ef4444;
  }
</style>
```

- [ ] **Step 2: Run the frontend typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors. (No automated component test exists for Button — the project has no jsdom/testing-library setup. Manual verification happens in Task 4.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/Button.svelte
git commit -m "fix: rewrite Button component — remove broken stub, implement variant/disabled/slot"
```

---

### Task 2: Create AvatarBadge.svelte

**Files:**
- Create: `frontend/src/lib/components/AvatarBadge.svelte`

Extracts the avatar circle rendering (initials fallback or `<img>` when `avatar_url` is set) from `NavBarAvatar` into a reusable component. Consumed by both `NavBarAvatar` and the Settings page.

- [ ] **Step 1: Create the file**

Write `frontend/src/lib/components/AvatarBadge.svelte`:

```svelte
<!--
  AvatarBadge
  Purpose: Renders a circular avatar — either the user's uploaded photo (avatar_url) or
    a coloured circle with initials derived from first_name/last_name.
  Used in: NavBarAvatar (36px), Settings page (32px).
  Props:
    - user (UserResponse): provides avatar_url, first_name, last_name
    - size (string): CSS length for the circle diameter, default '36px'
  Styling:
    Circle background #1f6feb (initials variant). Image variant: object-fit cover.
    Font-size is ~44% of the numeric size value, set via inline style.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

  export let user: UserResponse;
  export let size: string = '36px';

  $: initials = `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();

  // Parse the numeric portion of the size string (e.g. '36px' → 36) to derive font-size.
  $: numericSize = parseFloat(size);
  $: fontSize = `${(numericSize * 0.44).toFixed(1)}px`;
</script>

{#if user.avatar_url}
  <img
    src={user.avatar_url}
    alt=""
    class="avatar"
    style="width: {size}; height: {size};"
  />
{:else}
  <span
    class="avatar initials"
    style="width: {size}; height: {size}; font-size: {fontSize};"
  >
    {initials}
  </span>
{/if}

<style>
  .avatar {
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    flex-shrink: 0;
  }

  .initials {
    background: #1f6feb;
    color: #ffffff;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  img.avatar {
    object-fit: cover;
  }
</style>
```

- [ ] **Step 2: Run the frontend typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/AvatarBadge.svelte
git commit -m "feat: add AvatarBadge component — extracted avatar circle for reuse"
```

---

### Task 3: Update NavBarAvatar — use AvatarBadge, restyle dropdown

**Files:**
- Modify: `frontend/src/lib/components/NavBarAvatar.svelte`

Replace inline initials/image markup with `<AvatarBadge>`. Restyle the dropdown to white background with the project's omnidirectional drop shadow. Replace `<a>` nav items with `<NavLink>` components. Match Sign Out button to NavLink typography.

- [ ] **Step 1: Replace the full file**

Write `frontend/src/lib/components/NavBarAvatar.svelte`:

```svelte
<!--
  NavBarAvatar
  Purpose: User avatar shown on the right of the NavBar with a dropdown for the
    user's Dashboard, Settings, Help, and Sign out.
  Used in: NavBar
  Props:
    - user (UserResponse): current user
  Behaviour:
    - Clicking the avatar toggles a dropdown panel anchored below-right of the avatar.
    - Dropdown items: "Dashboard" (/dashboard), "Settings" (/settings), "Help" (/help), "Sign out".
    - Clicking outside the dropdown or pressing Escape closes it.
  Styling:
    Avatar: 36px circle (via AvatarBadge).
    Dropdown: white background, omnidirectional drop shadow matching PageCard/AlbumCard,
    NavLink components for nav items, matching button style for Sign out.
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { signOut } from '$lib/api/auth';
  import { currentUser } from '$lib/stores/user';
  import type { UserResponse } from '$lib/api/types';
  import AvatarBadge from '$lib/components/AvatarBadge.svelte';
  import NavLink from '$lib/components/NavLink.svelte';

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

  function handleSignOut() {
    signOut();
    currentUser.set(null);
    goto('/');
  }
</script>

<svelte:window on:click={handleWindowClick} on:keydown={handleKeydown} />

<div class="avatar-container" bind:this={containerEl}>
  <button class="avatar-button" on:click={toggle} aria-label="User menu" aria-expanded={open}>
    <AvatarBadge {user} size="36px" />
  </button>

  {#if open}
    <div class="dropdown" role="menu">
      <div class="dropdown-item"><NavLink href="/dashboard" label="Dashboard" /></div>
      <div class="dropdown-item"><NavLink href="/settings" label="Settings" /></div>
      <div class="dropdown-item"><NavLink href="/help" label="Help" /></div>
      <hr class="divider" />
      <button class="sign-out" role="menuitem" on:click={handleSignOut}>Sign out</button>
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
    display: flex;
    align-items: center;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    min-width: 180px;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
    z-index: 10;
  }

  .dropdown-item {
    padding: 0.5rem 1rem;
    display: block;
  }

  .divider {
    border: none;
    border-top: 1px solid #e2e2dc;
    margin: 0.25rem 0;
  }

  .sign-out {
    background: none;
    border: none;
    cursor: pointer;
    width: 100%;
    text-align: left;
    color: #232f3e;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-family: 'Ubuntu', sans-serif;
  }

  .sign-out:hover {
    text-decoration: underline;
  }
</style>
```

- [ ] **Step 2: Run the frontend typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/NavBarAvatar.svelte
git commit -m "feat: restyle NavBarAvatar dropdown — white card, NavLink items, AvatarBadge"
```

---

### Task 4: Rewrite Settings page

**Files:**
- Rewrite: `frontend/src/routes/settings/+page.svelte`

Full rewrite. Sidebar + content layout mirroring `/learn/[id]`. Sidebar has a "Personalisation" NavLink (active when `$page.url.pathname === '/settings'`). Content card has the Personalisation section: h1, hr, upload row (label left / AvatarBadge + Button right). Client-side image processing pipeline: 2 MiB gate → canvas centre-crop → 800×800 WEBP transcode → presigned PUT.

- [ ] **Step 1: Replace the full file**

Write `frontend/src/routes/settings/+page.svelte`:

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import PageCard from '$lib/components/PageCard.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import Button from '$lib/components/Button.svelte';
  import AvatarBadge from '$lib/components/AvatarBadge.svelte';
  import { requestAvatarUploadUrl, updateAvatar } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  const MAX_BYTES = 2 * 1024 * 1024; // 2 MiB

  let uploading = false;
  let error: string | null = null;
  let status: string | null = null;
  let fileInput: HTMLInputElement;

  $: isActive = (href: string) => $page.url.pathname === href;

  function processImage(file: File): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const objectUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(objectUrl);
        const cropSize = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - cropSize) / 2;
        const sy = (img.naturalHeight - cropSize) / 2;
        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 800;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }
        ctx.drawImage(img, sx, sy, cropSize, cropSize, 0, 0, 800, 800);
        canvas.toBlob(
          (blob) => {
            if (blob) resolve(blob);
            else reject(new Error('canvas.toBlob returned null'));
          },
          'image/webp',
          0.9
        );
      };
      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error('Image failed to load'));
      };
      img.src = objectUrl;
    });
  }

  async function handleFileChange() {
    const file = fileInput.files?.[0];
    if (!file) return;

    error = null;
    status = null;

    if (file.size > MAX_BYTES) {
      error = 'File must be under 2 MB.';
      fileInput.value = '';
      return;
    }

    uploading = true;
    status = 'Processing...';
    try {
      const blob = await processImage(file);
      status = 'Uploading...';

      const { upload_url, key } = await requestAvatarUploadUrl('image/webp');

      const putResponse = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'image/webp' },
        body: blob,
      });
      if (!putResponse.ok) {
        throw new Error('Upload to S3 failed');
      }

      const updatedUser = await updateAvatar(key);
      currentUser.set(updatedUser);
      status = 'Profile picture updated.';
    } catch (err) {
      console.error('Avatar upload failed:', err);
      if (err instanceof Error && err.message === 'Could not process image') {
        error = 'Could not process image. Please try a different file.';
      } else {
        error = 'Could not upload your profile picture. Please try again.';
      }
      status = null;
    } finally {
      uploading = false;
      fileInput.value = '';
    }
  }
</script>

<div class="settings-page">
  <PageCard as="aside" width="288px" padding="1.5rem 1rem">
    <nav aria-label="Settings sections">
      <div class="nav-item" class:active={isActive('/settings')}>
        <NavLink href="/settings" label="Personalisation" />
      </div>
    </nav>
  </PageCard>

  <PageCard as="main">
    <h1>Personalisation</h1>
    <hr />

    <div class="upload-row">
      <label for="avatar-trigger">Upload a profile picture</label>
      <div class="upload-controls">
        {#if $currentUser}
          <AvatarBadge user={$currentUser} size="32px" />
        {/if}
        <Button
          variant="primary"
          disabled={uploading}
          on:click={() => fileInput.click()}
        >
          Choose file
        </Button>
        <input
          type="file"
          id="avatar-trigger"
          accept="image/jpeg,image/png,image/webp"
          bind:this={fileInput}
          on:change={handleFileChange}
          disabled={uploading}
          style="display: none;"
        />
      </div>
    </div>

    <p aria-live="polite" class="status">{status ?? ''}</p>
    {#if error}
      <p role="alert" class="error">{error}</p>
    {/if}
  </PageCard>
</div>

<style>
  .settings-page {
    display: flex;
    gap: var(--gap-inner);
    height: 100%;
  }

  .settings-page > :global(aside.page-card) {
    flex: 0 0 288px;
  }

  .settings-page > :global(main.page-card) {
    flex: 1 1 auto;
    min-width: 0;
  }

  nav {
    display: flex;
    flex-direction: column;
  }

  .nav-item {
    padding: 0.4rem 0;
    font-size: 0.875rem;
  }

  .nav-item.active :global(a) {
    font-weight: 700;
    color: #232f3e;
  }

  h1 {
    margin: 0 0 0.75rem;
    font-size: 1.25rem;
    font-weight: 700;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  hr {
    border: none;
    border-top: 1px solid #e2e2dc;
    margin: 0 0 1.5rem;
  }

  .upload-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  label {
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.875rem;
    color: #232f3e;
  }

  .upload-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0.75rem 0 0;
    min-height: 1.25em;
    font-family: 'Ubuntu', sans-serif;
  }

  .error {
    font-size: 0.875rem;
    color: #ef4444;
    margin: 0.5rem 0 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
```

- [ ] **Step 2: Run the frontend typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run the full vitest suite to check for regressions**

```bash
cd frontend && npx vitest run
```

Expected: All existing tests pass (no component tests for settings — manual verification in Step 4).

- [ ] **Step 4: Manual verification — start dev server**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` (or whatever port Vite prints). Verify:

1. **Button component** — visit any page that uses `<Button>`. It should render correctly with the right colours; clicking shouldn't alert.
2. **NavBarAvatar dropdown** (requires being logged in) — click the avatar. The dropdown should be white with a drop shadow, no dark background. Dashboard/Settings/Help should render as NavLinks with the underline-on-hover animation. Sign Out should match their font/colour. Clicking Sign Out should clear the session and redirect to `/`.
3. **Settings sidebar** — navigate to `/settings`. The sidebar should appear on the left (288px white card), "Personalisation" NavLink rendered in bold (active state). Content card on the right with the h1, hr, and upload row.
4. **Upload row** — label on the left. If no avatar, only the Button appears on the right; if an avatar exists, the circular badge appears beside it. Button click opens the file picker.
5. **2 MiB gate** — pick a file over 2 MB. Error message "File must be under 2 MB." appears, no upload attempted.
6. **Image processing + upload** — pick a valid image. Status shows "Processing..." then "Uploading..." then "Profile picture updated." The NavBarAvatar badge updates immediately to the new image.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/settings/+page.svelte
git commit -m "feat: redesign Settings page — sidebar layout, AvatarBadge, canvas image processing"
```

---

## Self-Review

**Spec coverage:**
- Button rewrite → Task 1 ✓
- AvatarBadge new component → Task 2 ✓
- NavBarAvatar: AvatarBadge + white dropdown + NavLink items + Sign Out matching NavLink colour → Task 3 ✓
- Settings sidebar with Personalisation NavLink (active state) → Task 4 ✓
- Settings content: h1, hr, upload row (label left / badge+button right) → Task 4 ✓
- 2 MiB size gate → Task 4 ✓
- Canvas centre-crop to 800×800 WEBP → Task 4 ✓
- Always sends `content_type: 'image/webp'` → Task 4 ✓
- PUT uses processed Blob not original File → Task 4 ✓
- Object URL revoked after image loads → Task 4 ✓

**Placeholder scan:** No TBDs, no "similar to Task N", all code blocks complete.

**Type consistency:**
- `AvatarBadge` props (`user: UserResponse`, `size: string`) are defined in Task 2 and used with matching names/types in Tasks 3 and 4.
- `Button` props (`variant`, `disabled`, `on:click`) defined in Task 1, used in Task 4 with matching names.
- `requestAvatarUploadUrl('image/webp')` matches the existing `users.ts` signature `(contentType: string) => Promise<AvatarUploadUrlResponse>`.
- `$currentUser` is `UserResponse | null` — Task 4 guards the `<AvatarBadge>` render with `{#if $currentUser}`.
