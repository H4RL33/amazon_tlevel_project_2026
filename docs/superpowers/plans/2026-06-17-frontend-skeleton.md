# Frontend Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a branded skeleton shell — navbar, footer, and blank placeholder pages — in Amazon's style using SvelteKit, CSS animations, Ubuntu font, and a shared `NavLink` component.

**Architecture:** A shared `NavLink.svelte` component is consumed by both `Navbar.svelte` and `Footer.svelte`. The root `+layout.svelte` composes these around a `<slot />` and applies global styles. Four placeholder route pages each render a bare `<main>` heading.

**Tech Stack:** SvelteKit 2, Svelte 4, TypeScript, Vitest, plain CSS (scoped `<style>` blocks), Google Fonts (Ubuntu).

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create dir + copy | `frontend/static/assets/logo.png` | Serve logo via SvelteKit static handler |
| Modify | `frontend/src/app.html` | Add Google Fonts `<link>` tags |
| Create | `frontend/src/lib/components/NavLink.svelte` | Shared animated link |
| Create | `frontend/src/lib/components/Navbar.svelte` | Logo-left, links-right bar |
| Create | `frontend/src/lib/components/Footer.svelte` | Three-column footer |
| Modify | `frontend/src/routes/+layout.svelte` | Root layout + global styles |
| Modify | `frontend/src/routes/+page.svelte` | Home placeholder |
| Create | `frontend/src/routes/learn/+page.svelte` | Learn placeholder |
| Create | `frontend/src/routes/topics/+page.svelte` | Topics placeholder |
| Create | `frontend/src/routes/dashboard/+page.svelte` | Dashboard placeholder |
| Modify | `frontend/src/lib/scaffold.test.ts` | Component import smoke tests |

---

### Task 1: Copy logo to static assets

**Files:**
- Create dir + copy: `frontend/static/assets/logo.png`

The SvelteKit static adapter serves files from `frontend/static/` at the root URL. The logo lives at `assets/logo.png` in the repo root and needs to be available at `/assets/logo.png` in the browser.

- [ ] **Step 1: Create the static assets directory and copy the logo**

```bash
mkdir -p frontend/static/assets
cp assets/logo.png frontend/static/assets/logo.png
```

- [ ] **Step 2: Verify the file exists**

```bash
ls -lh frontend/static/assets/logo.png
```

Expected: file listed, non-zero size.

- [ ] **Step 3: Commit**

```bash
git add frontend/static/assets/logo.png
git commit -m "feat: add logo to static assets"
```

---

### Task 2: Add Google Fonts to app.html

**Files:**
- Modify: `frontend/src/app.html`

Ubuntu font must load before any page renders to avoid FOUT (flash of unstyled text). Add preconnect hints and the stylesheet link.

- [ ] **Step 1: Open `frontend/src/app.html`. It currently looks like:**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

- [ ] **Step 2: Replace the entire file with:**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
    <link
      href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap"
      rel="stylesheet"
    />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

- [ ] **Step 3: Run type-check to verify no errors introduced**

```bash
cd frontend && npm run check
```

Expected: no errors. (Warnings about existing stubs are fine.)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app.html
git commit -m "feat: add Ubuntu font via Google Fonts"
```

---

### Task 3: NavLink component

**Files:**
- Create: `frontend/src/lib/components/NavLink.svelte`
- Modify: `frontend/src/lib/scaffold.test.ts`

`NavLink` is a self-contained `<a>` tag with a CSS-only gradient underline animation. Both `Navbar` and `Footer` will import it — changing the animation means editing one file.

- [ ] **Step 1: Add a failing test to `frontend/src/lib/scaffold.test.ts`**

Append this block to the end of the file (after the existing `Stores` describe block):

```ts
describe('Components', () => {
  it('NavLink exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavLink.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: FAIL — module not found or export undefined.

- [ ] **Step 3: Create `frontend/src/lib/components/NavLink.svelte`**

```svelte
<script lang="ts">
  export let href: string;
  export let label: string;
</script>

<a {href}>{label}</a>

<style>
  a {
    position: relative;
    display: inline-block;
    color: #ffffff;
    text-decoration: none;
    font-family: 'Ubuntu', sans-serif;
  }

  a::after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -0.3em;
    width: 100%;
    height: 0.15em;
    border-radius: 9999px;
    background: linear-gradient(to right, #ff9900, #ffd700);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease-in-out;
  }

  a:hover::after {
    transform: scaleX(1);
  }
</style>
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: all tests PASS including the new NavLink test.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/NavLink.svelte frontend/src/lib/scaffold.test.ts
git commit -m "feat: add NavLink component with gradient hover animation"
```

---

### Task 4: Navbar component

**Files:**
- Create: `frontend/src/lib/components/Navbar.svelte`
- Modify: `frontend/src/lib/scaffold.test.ts`

The navbar is a flex row: logo anchored left, four `NavLink`s anchored right. It always renders at 64px height with `#232f3e` background.

- [ ] **Step 1: Add a failing test — append to the `Components` describe block in `frontend/src/lib/scaffold.test.ts`**

```ts
  it('Navbar exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });
```

The file's `Components` describe block should now look like:

```ts
describe('Components', () => {
  it('NavLink exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavLink.svelte');
    expect(mod.default).toBeDefined();
  });

  it('Navbar exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify the new test fails**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: FAIL on the Navbar test only.

- [ ] **Step 3: Create `frontend/src/lib/components/Navbar.svelte`**

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
</script>

<nav>
  <a href="/" class="logo-link">
    <img src="/assets/logo.png" alt="T Level Placements at Amazon" class="logo" />
  </a>
  <div class="links">
    <NavLink href="/" label="Home" />
    <NavLink href="/learn" label="Learn" />
    <NavLink href="/topics" label="Topics" />
    <NavLink href="/dashboard" label="Dashboard" />
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
  }
</style>
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/Navbar.svelte frontend/src/lib/scaffold.test.ts
git commit -m "feat: add Navbar component"
```

---

### Task 5: Footer component

**Files:**
- Create: `frontend/src/lib/components/Footer.svelte`
- Modify: `frontend/src/lib/scaffold.test.ts`

The footer uses the same `#232f3e` background as the navbar. Three CSS Grid columns (Navigation, About, Support). Column headings are styled in `#ff9900`. A thin rule and copyright line sit below the columns.

- [ ] **Step 1: Add a failing test — append to the `Components` describe block in `frontend/src/lib/scaffold.test.ts`**

The full `Components` describe block should now be:

```ts
describe('Components', () => {
  it('NavLink exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavLink.svelte');
    expect(mod.default).toBeDefined();
  });

  it('Navbar exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });

  it('Footer exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Footer.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify the new Footer test fails**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: FAIL on Footer test only.

- [ ] **Step 3: Create `frontend/src/lib/components/Footer.svelte`**

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
</script>

<footer>
  <div class="columns">
    <div class="column">
      <h3 class="column-heading">Navigation</h3>
      <div class="column-links">
        <NavLink href="/" label="Home" />
        <NavLink href="/learn" label="Learn" />
        <NavLink href="/topics" label="Topics" />
        <NavLink href="/dashboard" label="Dashboard" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">About</h3>
      <div class="column-links">
        <NavLink href="#" label="About This Project" />
        <NavLink href="#" label="T-Level Programme" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">Support</h3>
      <div class="column-links">
        <NavLink href="#" label="Help" />
        <NavLink href="#" label="Contact Us" />
      </div>
    </div>
  </div>
  <div class="bottom-bar">
    <p>© 2026 Amazon T-Level Project</p>
  </div>
</footer>

<style>
  footer {
    background: #232f3e;
    color: #ffffff;
    padding: 2rem 1.5rem 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .columns {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    padding-bottom: 2rem;
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .column-heading {
    margin: 0 0 0.75rem;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #ff9900;
  }

  .column-links {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .bottom-bar {
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    padding: 1rem 0;
    text-align: center;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }

  .bottom-bar p {
    margin: 0;
  }
</style>
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/Footer.svelte frontend/src/lib/scaffold.test.ts
git commit -m "feat: add Footer component with three-column layout"
```

---

### Task 6: Root layout

**Files:**
- Create: `frontend/src/routes/+layout.svelte`

The root layout wraps every page with `<Navbar />`, `<slot />`, and `<Footer />`. It also applies global CSS resets and body defaults. Note: `+layout.ts` already exists (disables SSR/prerender) — do not modify it.

- [ ] **Step 1: Create `frontend/src/routes/+layout.svelte`**

```svelte
<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import Footer from '$lib/components/Footer.svelte';
</script>

<Navbar />
<slot />
<Footer />

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
    background: #f5f5f0;
    color: #232f3e;
  }
</style>
```

- [ ] **Step 2: Run type-check**

```bash
cd frontend && npm run check
```

Expected: no errors. (Existing stub warnings in other components are acceptable.)

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: add root layout with Navbar and Footer"
```

---

### Task 7: Placeholder pages

**Files:**
- Modify: `frontend/src/routes/+page.svelte`
- Create: `frontend/src/routes/learn/+page.svelte`
- Create: `frontend/src/routes/topics/+page.svelte`
- Create: `frontend/src/routes/dashboard/+page.svelte`

Each page is a minimal `<main>` block — a heading and a "coming soon" line. The `max-width` and auto margins keep content readable without a sidebar.

- [ ] **Step 1: Replace `frontend/src/routes/+page.svelte` with:**

```svelte
<main>
  <h1>Home</h1>
  <p>Coming soon.</p>
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 2: Create `frontend/src/routes/learn/+page.svelte`**

```svelte
<main>
  <h1>Learn</h1>
  <p>Coming soon.</p>
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 3: Create `frontend/src/routes/topics/+page.svelte`**

```svelte
<main>
  <h1>Topics</h1>
  <p>Coming soon.</p>
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 4: Create `frontend/src/routes/dashboard/+page.svelte`**

```svelte
<main>
  <h1>Dashboard</h1>
  <p>Coming soon.</p>
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 5: Run type-check**

```bash
cd frontend && npm run check
```

Expected: no errors.

- [ ] **Step 6: Run tests**

```bash
cd frontend && npm run test:unit -- --run
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/routes/+page.svelte \
        frontend/src/routes/learn/+page.svelte \
        frontend/src/routes/topics/+page.svelte \
        frontend/src/routes/dashboard/+page.svelte
git commit -m "feat: add placeholder pages for Home, Learn, Topics, Dashboard"
```
