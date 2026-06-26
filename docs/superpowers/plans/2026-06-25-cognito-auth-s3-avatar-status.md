# Cognito Auth + S3 Avatar — Status

**Plan:** `docs/superpowers/plans/2026-06-24-cognito-auth-s3-avatar.md`
**Spec:** `docs/superpowers/specs/2026-06-24-cognito-auth-s3-avatar-design.md`
**Result:** Merged to `dev` at `6cdd1c9` on 2026-06-25.

## Done

All 13 implementation tasks from the plan, each through implementer → spec-compliance
review → code-quality review, with fixes applied wherever a review found a real issue.

**Backend** (48/48 tests passing):
- Real Cognito JWT validation in `get_current_user` via JWKS (`backend/app/dependencies/auth.py`)
- `avatar_s3_key` column + migration, `avatar_url` on `UserResponse`, `build_user_response` helper
- `/auth/sync` extracting real claims from the bearer token
- `user_service.get_me` / `set_topics` / `get_topics`
- `content_service.get_presigned_url`
- Avatar upload endpoints: `POST /users/me/avatar-upload-url`, `PATCH /users/me/avatar`

**Frontend** (42/42 vitest passing, 0 typecheck errors, build clean):
- `UserResponse.avatar_url` type + story file updates
- PKCE login (`getCognitoLoginUrl`, `exchangeCode`, `syncUser`, `signOut`) in `lib/api/auth.ts`
- Bearer token auto-attached to every `apiFetch` call
- `/auth/callback` route + Navbar "Log in" wired to real Cognito Hosted UI
- `currentUser` rehydration from stored token on app load (`+layout.svelte`)
- `NavBarAvatar` image rendering + Settings page avatar upload UI

**Fixes applied during review (not just rubber-stamped):**
- Security: `set_avatar` now rejects any `avatar_s3_key` not under `avatars/{user.id}/` —
  without this, a client could point their avatar at arbitrary S3 bucket contents and
  have it served back via a presigned GET URL.
- Correctness: JWT payload decoding used raw `atob`, which can't handle base64url
  characters (`-`/`_`) that real Cognito tokens contain — added `decodeJwtPayload` with
  proper base64url→base64 conversion and padding.
- Accessibility: avatar upload status had no `aria-live` region, so screen-reader users
  got no feedback on success; also the file input wasn't reset after a failed upload,
  blocking retry with the same file.
- Consistency: `/login` was still a static "coming soon" stub even though the Navbar's
  own "Log in" link already drove a real Cognito flow — wired it to the same
  `getCognitoLoginUrl()` path.
- Several smaller cleanups: reused `apiFetch` in `syncUser` instead of duplicating fetch
  logic, checked `response.ok` in `exchangeCode`, tightened test exception types.

## Not done

**Task 14 — manual end-to-end verification against real Cognito.** This is the only
remaining step and requires the user, not an agent:

1. `terraform apply` (infra: Cognito callback URLs, schema attributes, S3 CORS — described
   in the design spec, not part of this plan since the agent has no AWS credentials).
2. Populate `backend/.env` with real `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`,
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
3. Populate `docker-compose.yml`'s `VITE_COGNITO_DOMAIN` / `VITE_COGNITO_CLIENT_ID` /
   `VITE_COGNITO_REDIRECT_URI` build args.
4. Run migrations (`docker compose exec backend poetry run alembic upgrade head`).
5. Walk the flow in a browser: sign up via Hosted UI → redirected to `/auth/callback` →
   Navbar shows initials → upload an avatar in `/settings` → Navbar avatar updates →
   refresh → still logged in, avatar persists → open the avatar's presigned URL directly
   to confirm it's genuinely served from S3.

If any step fails, the plan's own guidance is to fix forward with a new task/commit
rather than reopening earlier ones, and record what broke for next time.

## Known, accepted tech debt (out of scope, not blocking)

- Three different naming conventions for "generate a presigned S3 URL" exist across
  `content_service.get_presigned_url`, `user_service._generate_presigned_get_url`, and
  `user_service._generate_presigned_put_url`. The plan explicitly scoped reconciling
  this as out of bounds.
- `_cached_jwks()` has no TTL/invalidation — a Cognito key-rotation event would wedge
  auth until process restart. Acceptable for MVP.
- No client-side file-size cap on avatar uploads before hitting the presigned PUT URL.
- `content_service.list_content` / `get_content` / `get_s3_key` remain unimplemented
  stubs — pre-existing gap, unrelated to this feature.

## Next

Once Task 14 is run (or the user decides to defer it), move to sub-project 2
(Home/Dashboard) per the showcase plan.
