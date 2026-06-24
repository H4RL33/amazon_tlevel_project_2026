# Backend implementation masterplan

Date: 2026-06-24

## Context

The backend (`backend/app/`) is fully scaffolded — every router, schema, and service
file from CLAUDE.md's structure already exists — but only `album_service.py` (built in
the previous chapter, see
[`2026-06-22-album-side-model-design.md`](2026-06-22-album-side-model-design.md)) has a
real implementation. `auth_service`, `content_service`, `feed_service`,
`topic_service`, and `user_service` are all `NotImplementedError` stubs. The Forum
(Post/Like/Save) and the Dynamic Mentor (Bedrock) have no code at all yet — not even
stubs.

This document sequences the remaining backend work into seven components. It is a
roadmap, not an implementation plan: each component below gets its own
brainstorming → design spec → implementation plan → subagent-driven-implementation
cycle when its turn comes, the same process used for Album/Side. This doc exists so
that sequencing and cross-component dependencies are decided once, up front, rather
than re-litigated at the start of each chapter.

> **2026-06-24 update:** Added Component 5, Gamification/XP, surfaced while planning
> the frontend Dashboard page (see
> [`2026-06-24-frontend-masterplan.md`](2026-06-24-frontend-masterplan.md)) — the
> Dashboard needs XP/stats data that nothing in the backend currently produces. The
> Forum and Dynamic Mentor shift from 5/6 to 6/7 accordingly.

## Components

### 1. Auth & Identity

Replaces the `get_current_user`/`get_current_user_optional` `NotImplementedError`
stubs in `app/dependencies/auth.py` with real Cognito JWT validation, fixes
`auth_service.sync_user`'s known gap (it currently passes empty strings for
`cognito_sub`/`email` instead of extracting them from the validated token — see
CLAUDE.md's "Known gap"), and derives the age tier (Exploring/Learning/Career) from
the DOB Cognito attribute at request time, exposed on `User` so routers can gate
access.

Also fixes `app/routers/topics.py`, which has the same router-level
`dependencies=[Depends(get_current_user)]` bug that `content.py` had — found during
the Album/Side chapter and deliberately left out of scope there since `topics.py`
wasn't part of that spec. Topics/T-Levels must be public per CLAUDE.md, same as
Snippets and Albums.

**Depends on:** nothing — this is the foundation everything else needs.

### 2. User Profiles

Real implementation of `user_service` (`get_me`, `set_topics`, `get_topics`). The
`User` model currently has no `avatar`, `header_image`, or `bio` columns — CLAUDE.md's
MVP scope calls for a profile page with avatar, header image, and bio (max 500 chars,
per `UserProfileBio`'s spec in the component reference table). This component adds
those columns and a migration. DOB itself is **not** a DB column — it stays a Cognito
user attribute per CLAUDE.md, with only the derived age tier exposed by Component 1.

**Depends on:** Auth (needs `get_current_user` working for real to be testable
end-to-end; age tier may gate which profile fields are editable).

### 3. Content Browsing

Real implementation of `content_service` (list/get Snippets, presigned S3 audio URLs)
and `topic_service` (list/get Topics and T-Levels). Album/Side (the pathway layer on
top of Content) is already done. This component is the layer underneath it.

**Depends on:** Auth, for the public/private boundary pattern established when fixing
`content.py` and `topics.py` (both routers must stay public — no new dependency here,
just continuing the existing pattern correctly).

### 4. Feed & Progress

Real implementation of `feed_service` (`get_feed`, `get_progress`, `upsert_progress`)
— the personalised feed and "continue reading" surface that backs The Library.

**Depends on:** Auth (all three routes require a real user), Content Browsing (the
feed surfaces `Content` rows).

### 5. Gamification/XP

CLAUDE.md describes the platform as gamified ("rewarded for how many chunks they
consume"), and the frontend already has `XPBadge`/`MentorBadge`/`ProgressBar` stub
components and a Dashboard page intended to show XP-over-time, Albums-enrolled count,
and Snippets-read count — but nothing in the backend currently models or computes XP.
This component adds whatever's needed to make those real: most likely XP awarded on
Snippet completion and/or Album completion (derived from existing
`UserContentProgress`/`AlbumEnrolment` data rather than a new mutable "current XP"
column, to avoid denormalised state going stale — consistent with how Album progress
was computed in the Album/Side chapter), plus a stats endpoint the Dashboard can call.
Exact XP rules (how much per Snippet, bonuses for Album completion, etc.) are a design
question for this component's own brainstorming, not decided here.

**Depends on:** Auth, Feed & Progress (XP/stats are derived from progress and
enrolment data, so this component is naturally sequenced right after it).

### 6. The Forum

New models (`Post`, `Like`, `Save` — no comments, per CLAUDE.md's explicit
"no comments feature" constraint), a new router, and a new service. Age-gated:
Exploring tier gets no access, Learning tier is read-only (own cohort only), Career
tier gets full read/write. This is the social feed described in CLAUDE.md as a
nice-to-have — sequenced after the core Library-facing components, not before.

**Depends on:** Auth (age tier drives the gating rules), Content Browsing (posts may
reference/share Snippets — to be confirmed during that component's own design).

### 7. Dynamic Mentor (Bedrock)

New chat backend: conversation history persistence, Amazon Bedrock Knowledge
Base/RAG integration, Socratic-framework prompting. Per CLAUDE.md, student telemetry
must stay within the private VPC — no external data retention (ICO Children's Code).
Sequenced last — it's the most infrastructure-heavy piece (Bedrock KB setup is partly
a Terraform/infra concern, not pure backend logic) and benefits from Auth/age-tier
being solid first, since consent handling for AI profiling is mandatory per CLAUDE.md
("Never expose AI profiling features to any user without consent handling").

**Depends on:** Auth (user identity + age tier + consent state).

## Sequencing rationale

Auth is first because every other component's auth boundary depends on it being real,
not stubbed — building Profiles, Feed, or the Forum against a stub risks rework once
real JWT validation and age-tier derivation land. Content Browsing comes next because
it's the most self-contained remaining piece and Feed/Forum both read from it. Feed
comes before Gamification/XP because XP/stats are computed from progress and
enrolment data that Feed & Progress establishes. The Forum stays after Gamification
because it's required MVP scope item 2 (Content/Feed/Profiles) and explicitly-scoped
item 3 (Forum) ordering from CLAUDE.md, and because Gamification is needed to unblock
the frontend Dashboard chapter, which is more immediately useful than the
nice-to-have Forum. The Dynamic Mentor is last both because it's scope item 4 in
CLAUDE.md and because it's the most architecturally novel piece (Bedrock integration,
RAG, consent handling) — better attempted once the rest of the auth/data patterns are
settled.

## Cross-cutting process notes

- Each component repeats the cycle used for Album/Side: brainstorming → design spec
  in `docs/superpowers/specs/` → implementation plan in `docs/superpowers/plans/` →
  subagent-driven-development execution with two-stage (spec compliance, then code
  quality) review per task, in an isolated git worktree/branch.
- Reuse the existing test infrastructure: the `db_session`/`client`/
  `authenticated_client` fixtures in `tests/conftest.py`, the local Postgres
  container pattern, and the CI `postgres:17-alpine` service container added to
  `backend.yml` during Album/Side.
- `app/dependencies/auth.py`'s eventual real implementation is the single highest-
  leverage piece of remaining work — every other component's tests currently rely on
  FastAPI dependency overrides (`get_current_user`/`get_current_user_optional`)
  standing in for it, and that pattern should continue to work unchanged once the
  real implementation lands (the override mechanism doesn't care whether the
  overridden function is a stub or real).

## Out of scope (for this masterplan and, by default, for every component's spec)

- Actual AWS infrastructure provisioning/wiring (Cognito user pool config, Bedrock
  Knowledge Base setup, S3 bucket policies) — these are Terraform/infra concerns
  tracked separately from backend application logic. A component's spec may need to
  *assume* infra exists (e.g. Component 6 assumes a Bedrock KB is reachable) but
  provisioning it is not part of these specs unless explicitly pulled in later.
- Frontend integration for any component — frontend work is tracked separately.
- Real end-to-end testing against live AWS services (Cognito, Bedrock, S3) — test
  suites use mocks/stubs/local equivalents per component, consistent with the
  project's current test patterns.
