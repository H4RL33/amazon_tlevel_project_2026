# Living Campus — CLAUDE.md

Amazon T-Level Project 2026. Exeter College. Team: Ahad Afzaal, Bea Walker, Bobby Dauton, Ellie Thomas, Harley Welsh, Isaac Northan.

**What we're building:** "Living Campus" — an edtech platform that helps UK students (ages 11–18), parents, and teachers discover and engage with Amazon's T-Level courses. The platform is gamified, social, and AI-assisted; the UX metaphor is a lively university campus rather than a sterile LMS.

---

## Architecture

```
amazon_tlevel_project_2026/
├── backend/          FastAPI + PostgreSQL + Alembic + Poetry
├── frontend/         SvelteKit + TypeScript
├── infrastructure/   Terraform (AWS: ECS, RDS, Cognito, S3, ECR)
└── docker-compose.yml  Local dev (db + backend + frontend)
```

**Local services:**

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000      |
| Backend  | http://localhost:8000      |
| API docs | http://localhost:8000/docs |
| Database | localhost:5432             |

**Local setup:**

```sh
docker compose up --build -d
docker compose exec backend poetry run alembic upgrade head
docker compose exec backend poetry run python seed.py  # optional: seed topics + T-levels
```

---

## Domain Terminology

These are the canonical terms. Use them in code, routes, and comments.

| Term | Meaning | DB model |
|------|---------|----------|
| **Snippet** | A single short-form piece of content (article / audio / video). Publicly accessible without an account. | `Content` |
| **Album** | A curated set of Snippets forming a learning pathway (e.g. "Cloud Computing T-Level"). Requires an account to enrol. | not yet modelled |
| **Side** | A section/chapter within an Album (analogous to a vinyl record's Side A/B — plays into the Album metaphor). Tentative term; may evolve. | not yet modelled |
| **The Forum** | The social feed area (LinkedIn/TikTok-style). Age-gated. | — |
| **The Library** | The personal learning dashboard. Houses the user's enrolled Albums, progress, and the AgentChat. | — |
| **Dynamic Mentor** | The personalised AI tutor (Amazon Bedrock, RAG, Socratic framework). Lives at the bottom of the CTASidebar. | — |
| **Living Campus** | The overarching UX framework/brand. Not a code concept. | — |

**Note:** The codebase currently uses `Content` for what the docs call Snippet, and `Topic` / `TLevel` for the subject-area taxonomy. When adding new models, name them `Album`, `Side`, `Post`, etc. — not `Track`, `Module`, `Piece` (those are deprecated terms from earlier drafts).

---

## MVP Scope (prototype)

All of these are in scope. Social features are a nice-to-have — prioritise the others first.

1. **Auth + user profiles** — Cognito registration/login, DOB → age tier, profile page (avatar, header image, bio)
2. **Content browsing** — Snippets and Albums publicly accessible without login; authenticated users can enrol in Albums and track progress
3. **Social feed (The Forum)** — Post, like, save; age-gated *(nice-to-have)*
4. **Dynamic Mentor (Bedrock)** — Personalised Socratic AI tutor in The Library sidebar

Content is seeded manually via `backend/seed.py`. There is no admin CMS for this phase.

---

## Age Tiers (mandatory — legal compliance)

Age is collected as DOB at Cognito signup and stored as a Cognito user attribute. The tier is derived at runtime.

| Tier | Ages | Access |
|------|------|--------|
| Exploring | 11–13 | Content browsing, The Library, AgentChat. No social. |
| Learning | 14–16 | + Read-only Quad (see posts from their cohort only). |
| Career | 16–18 | Full Quad (can post, like, save). Career pipeline track. |

**These restrictions are non-negotiable.** They are required by:
- UK "Australia-Plus" under-16 social media ban (educational service exemption requires tiered access)
- ICO Children's Code (AI profiling of minors)
- UK GDPR

Never expose social write features to users under 16. Never expose AI profiling features to any user without consent handling. Enforce age tier server-side — never rely on the frontend alone.

---

## Accessibility (mandatory)

**WCAG 2.2 AA compliance is a legal requirement** under the Equality Act 2010 and the Public Sector Accessibility Regulations 2018. Inaccessible dynamic web elements have resulted in UK court settlements (Stephen Campbell v HSCNI, £3k).

- All images must have `alt` text.
- All interactive elements must be keyboard-navigable.
- The AudioPlayer component must support a keyboard shortcut (for visually impaired users).
- Colour contrast ratios must meet AA thresholds.
- Use semantic HTML elements.

---

## Backend Structure

```
backend/app/
├── config.py         Pydantic settings (env vars via .env)
├── database.py       Async SQLAlchemy engine + session factory
├── main.py           FastAPI app, CORS, router registration
├── models/           SQLAlchemy ORM models
│   ├── user.py       User, UserTopicInterest
│   ├── content.py    Content (= Snippet), Tag, ContentType enum
│   ├── progress.py   UserContentProgress
│   ├── topic.py      Topic (subject area with accent_colour)
│   └── t_level.py    TLevel (a T-Level offering, belongs to a Topic)
├── schemas/          Pydantic request/response schemas
├── routers/          FastAPI route handlers (auth, users, topics, content, feed)
├── services/         Business logic (one file per router)
└── dependencies/     FastAPI dependency injection (auth.py etc.)
```

**Auth flow:** AWS Cognito handles login/registration. After token exchange, the frontend calls `POST /auth/sync` to upsert the user row. Subsequent requests pass the Cognito JWT in `Authorization: Bearer <token>`; the backend validates it.

**Known gap:** `routers/auth.py` currently passes empty strings for `cognito_sub` and `email` to `auth_service.sync_user` — the JWT extraction is not yet implemented. Fix this before the auth flow can work end-to-end.

**Adding new models:**
1. Create `backend/app/models/<name>.py`
2. Import it in `backend/app/models/__init__.py`
3. Generate a migration: `poetry run alembic revision --autogenerate -m "add <name>"`
4. Apply: `poetry run alembic upgrade head`

---

## Frontend Structure

```
frontend/src/
├── routes/           SvelteKit file-based routing
│   ├── +layout.svelte / +layout.ts   Root layout
│   ├── +page.svelte                  Home / dashboard
│   ├── dashboard/                    Authenticated dashboard
│   ├── learn/                        Album / Snippet browsing
│   ├── topics/                       Topic discovery
│   └── api/                          Internal API routes (SvelteKit server endpoints)
└── lib/
    ├── components/   Reusable UI components
    └── stores/       Svelte stores (global state)
```

### UI Component Reference

These are the planned components per the design documentation. Implement them in `frontend/src/lib/components/`.

| Component | Purpose |
|-----------|---------|
| `NavBar` | Top bar with navigation links and NavBarAvatar |
| `NavLink` | Nav link with orange-yellow gradient underline on active/hover |
| `NavBarAvatar` | User avatar circle with dropdown (account, settings, dashboard, help) |
| `Footer` | Static footer with columns and copyright |
| `NavSidebar` | Left sidebar with stacked NavLinks (settings/dashboard menus) |
| `CTASidebar` | Main personalised sidebar: welcome message, resume widget, two AlbumCards, three SnippetCards, AgentChat |
| `AlbumCard` | Wide card to open an Album — icon, title, CTA, progress-out-of indicator, progress bar |
| `SnippetCard` | Square card to open a Snippet — centred icon + title |
| `AgentChat` | Input field for the AI tutor; accent line along bottom in orange-yellow gradient |
| `PostCard` | Forum post: poster info (avatar, name, role) + content (text/image/video) + actions (like, save) |
| `UserProfileHeader` | Banner image + avatar + name + subtitle (LinkedIn-style) |
| `UserProfileBio` | Free-text bio, max 500 chars |
| `AudioPlayer` | Card-like audio player on a Snippet; keyboard shortcut to toggle |
| `AlbumProgressWidget` | Top-left widget on an Album view: title + progress bar |
| `SnippetTitleBar` | Top bar within a Snippet: current title + reading progress bar along bottom |
| `AlbumSidebar` | Sidebar within an Album: lists Sides and their constituent Snippets |

**Brand gradient:** orange-yellow (`#F97316` → `#FACC15` or similar). Used on NavLink underlines, progress bars, and the AgentChat accent line. Confirm exact values with the designer.

---

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `backend.yml` | Push/PR to `main` touching `backend/**` | Ruff lint + autofix, pytest |
| `frontend.yml` | Push/PR to `main` touching `frontend/**` | Prettier + ESLint autofix, vitest |
| `terraform.yml` | Push/PR touching `infrastructure/**` | Plan on PR (posts comment), apply on merge |
| `release-backend.yml` | PR merged to `main` with label `bump-backend:{patch\|minor\|major}` | Bumps `backend/VERSION`, tags, pushes Docker image to GHCR |
| `release-frontend.yml` | PR merged to `main` with label `bump-frontend:{patch\|minor\|major}` | Same for frontend |

**Known issue:** The backend `test` job has no PostgreSQL service container, so any test that hits the DB will fail in CI. Add a `services: postgres:` block when writing DB-dependent tests.

---

## Key Constraints and Gotchas

- **`backend/.env` is gitignored.** Copy from `backend/.env.example` to create it locally.
- **Cognito user pool is in `eu-west-2`** (London). All AWS resources are in `eu-west-2`.
- **S3 is used for media blobs** (Snippet images/videos/audio, user avatars/headers). The bucket name is injected via `S3_BUCKET_NAME` env var.
- **Bedrock for AgentChat:** Amazon Bedrock Knowledge Base is used for the RAG pipeline. Student telemetry must stay within the private VPC — no external data retention (ICO Children's Code requirement).
- **No comments feature.** The social feed has likes and saves, but no comments. Do not implement commenting.
- **Snippets are public.** Any route serving Snippet content must not require authentication. Albums and The Library require authentication.
- **Age tier must be enforced server-side.** The `get_current_user` dependency should expose the user's age tier so routers can gate access.
