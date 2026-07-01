# Settings UI Polish — Design Spec

**Date:** 2026-06-26
**Scope:** Button component rewrite, AvatarBadge extraction, NavBarAvatar dropdown restyle, Settings page redesign, client-side image processing pipeline.

---

## 1. Button.svelte rewrite

The current file is a broken stub (duplicate `<script>` blocks, hardcoded `onclick=alert`, renders all three variants simultaneously). Replace with a proper implementation:

**Props:**
- `variant: 'primary' | 'secondary' | 'danger'` — default `'primary'`
- `disabled: boolean` — default `false`
- `type: 'button' | 'submit' | 'reset'` — default `'button'`

**Slot:** default — button label/content.

**Events:** forwards native `on:click`.

**Styling:**
- `font-family: 'Ubuntu', sans-serif`
- `border-radius: 6px`
- `padding: 0.5rem 1.25rem`
- `font-size: 0.875rem`
- `cursor: pointer`
- `border: none`
- `color: #ffffff`
- `primary` bg: `#1f6feb`
- `secondary` bg: `#21262d`
- `danger` bg: `#ef4444`
- `disabled`: `opacity: 0.5; cursor: not-allowed`

---

## 2. AvatarBadge.svelte (new component)

Extract the avatar-circle rendering from `NavBarAvatar` into a standalone component. Both `NavBarAvatar` and the Settings page use it.

**Props:**
- `user: UserResponse` — used for `avatar_url`, `first_name`, `last_name`
- `size: string` — CSS length, default `'36px'`

**Rendering:**
- If `user.avatar_url` is set: `<img src={user.avatar_url} alt="" class="avatar">` (decorative, alt empty)
- Otherwise: `<span class="avatar">{initials}</span>` — initials from `first_name.charAt(0) + last_name.charAt(0)`, uppercased
- Circle: `border-radius: 50%`, `width`/`height` from `size` prop, `background: #1f6feb` (initials variant), `color: #ffffff`, `font-size` scaled relative to size (approx 44% of size), `font-weight: 700`, `display: flex; align-items: center; justify-content: center`
- Image variant: `object-fit: cover`, `border-radius: 50%`, same `width`/`height`

**NavBarAvatar update:** import `AvatarBadge`, replace the inline initials/image markup with `<AvatarBadge {user} size="36px" />`.

---

## 3. NavBarAvatar dropdown restyle

**Remove:** dark background (`#161b22`), dark border (`#21262d`), light text (`#c9d1d9`).

**Add:**
- `background: #ffffff`
- `box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35)` (matches PageCard / AlbumCard)
- No border

**Nav items (Dashboard, Settings, Help):** replace `<a>` tags with `<NavLink>` components — Ubuntu font, `#232f3e`, orange-gradient underline on hover.

**Sign out:** `<button>` styled to match NavLink visually — Ubuntu font, `#232f3e`, `font-size: 0.875rem`, `background: none; border: none; cursor: pointer; padding: 0.5rem 1rem; text-align: left; width: 100%`. No special color (matches nav links, per user decision).

**Divider:** `<hr>` before Sign Out, `border: none; border-top: 1px solid #e2e2dc` (matches `SideHeader` divider).

---

## 4. Settings page redesign

### Layout

Mirrors `/learn/[id]`: a flex row with a 288px `<PageCard as="aside">` on the left and a `<PageCard as="main">` filling the rest.

```
.settings-page { display: flex; gap: var(--gap-inner); height: 100%; }
aside: flex: 0 0 288px
main: flex: 1 1 auto; min-width: 0
```

### Sidebar

A `<PageCard as="aside" width="288px" padding="1.5rem 1rem">` containing a `<nav>` with a single `<NavLink href="/settings" label="Personalisation" />`. Active state: bold, `#232f3e`. Additional sections (e.g. Account, Privacy) can be added as more NavLinks in future.

Active link detection: compare `$page.url.pathname` to the link's href.

### Content: Personalisation section

Inside `<PageCard as="main">`:

```
<h1>Personalisation</h1>
<hr />
```

Upload row:
```
<div class="upload-row">
  <label for="avatar-input">Upload a profile picture</label>
  <div class="upload-controls">
    <AvatarBadge user={$currentUser} size="32px" />
    <Button variant="primary" on:click={() => fileInput.click()}>Choose file</Button>
    <input type="file" id="avatar-input" accept="image/jpeg,image/png,image/webp" bind:this={fileInput} on:change={handleFileChange} disabled={uploading} style="display:none" />
  </div>
</div>
```

**Upload row layout:**
- `display: flex; align-items: center; justify-content: space-between`
- Left: `<label>` — Ubuntu, `0.875rem`, `#232f3e`
- Right (`.upload-controls`): `display: flex; align-items: center; gap: 0.75rem` — AvatarBadge + Button

**`<hr>` style:** `border: none; border-top: 1px solid #e2e2dc; margin: 0.75rem 0 1.5rem`

**`<h1>` style:** `font-size: 1.25rem; font-weight: 700; color: #232f3e; margin: 0`

**Status/error:** `<p aria-live="polite">` for status, `<p role="alert">` for errors, as before.

The file input is visually hidden (`.sr-only`) and triggered programmatically by the Button's click handler.

---

## 5. Client-side image processing

Inserted between file selection and presigned URL request in `handleFileChange`.

**Steps:**
1. **Size gate:** `if (file.size > 2 * 1024 * 1024)` → set error `'File must be under 2 MB.'`, return early. No processing attempted.
2. **Load image:** `URL.createObjectURL(file)` → `new Image()` → await `img.onload`.
3. **Centre-crop to square:** `const size = Math.min(img.naturalWidth, img.naturalHeight)`, `sx = (img.naturalWidth - size) / 2`, `sy = (img.naturalHeight - size) / 2`.
4. **Canvas resize:** 800×800 canvas, `ctx.drawImage(img, sx, sy, size, size, 0, 0, 800, 800)`.
5. **WEBP transcode:** `canvas.toBlob(blob => ..., 'image/webp', 0.9)` — always outputs WEBP.
6. **Revoke object URL** after image loads (prevent memory leak).
7. **Presigned URL:** always requests `content_type: 'image/webp'`.
8. **PUT:** uses the processed `Blob`, not the original `File`.

**Error handling:** wrap steps 2–5 in try/catch; any canvas failure shows `'Could not process image. Please try a different file.'`.

**Helper:** `processImage(file: File): Promise<Blob>` — pure function, no side effects, defined in the same settings page file (not exported; used only here).

---

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/components/Button.svelte` | Full rewrite |
| `frontend/src/lib/components/AvatarBadge.svelte` | New component |
| `frontend/src/lib/components/NavBarAvatar.svelte` | Import AvatarBadge; restyle dropdown |
| `frontend/src/routes/settings/+page.svelte` | Full rewrite with sidebar layout + image processing |

No backend changes. No new routes. No new API calls beyond what already exists.
