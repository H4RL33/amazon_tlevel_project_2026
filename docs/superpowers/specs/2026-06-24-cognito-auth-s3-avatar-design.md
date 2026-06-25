# Cognito Auth + S3 Avatar — Design

Date: 2026-06-24
Status: Approved for planning
Demo target: local docker-compose (localhost:3000 / localhost:8000), real AWS Cognito + S3 behind it.

## Goal

Replace the "Log in" navbar link with a real Cognito Hosted UI login flow, and once
logged in, let a user upload a profile picture that's stored in S3 and rendered by
`NavBarAvatar` instead of initials. This is the first of three sub-projects building
toward tomorrow's demo; the others (merged Home/Dashboard, Cloud Computing content
expansion) are separate specs and depend on this one only for the `currentUser` /
`avatar_url` shape, not on its implementation.

## Out of scope

- Deployed ECS/ALB demo path — only local docker-compose needs to work.
- New S3 bucket — reuse `exeaws26-content-{env}` under an `avatars/{user_id}` prefix.
- Avatar cropping/resizing, file-type validation beyond a basic allowlist.
- Refresh-token rotation / silent renewal — id_token good for the session length of a demo.

## Infra (Terraform — applied manually by the user, not by Claude)

`infrastructure/modules/auth/main.tf`:
- Add `"http://localhost:3000/auth/callback"` to `aws_cognito_user_pool_client.main.callback_urls`
  (alongside the existing ALB callback — `docker-compose.yml` already sets
  `VITE_COGNITO_REDIRECT_URI=http://localhost:3000/auth/callback`, anticipating this).
- Add `"http://localhost:3000/"` to `logout_urls`.
- Add `schema` blocks for `given_name` and `family_name` as required, mutable standard
  attributes, so the Hosted UI signup form collects first/last name.

`infrastructure/modules/storage/main.tf`:
- Add an `aws_s3_bucket_cors_configuration` for the content bucket allowing `GET`/`PUT`
  from `http://localhost:3000`, so the browser can PUT an avatar directly via a
  presigned URL.

After `terraform apply`, the user wires the resulting `user_pool_id`, `client_id`, and
`hosted_ui_domain` outputs into `backend/.env` and `docker-compose.yml`'s
`VITE_COGNITO_DOMAIN` / `VITE_COGNITO_CLIENT_ID` build args.

## Backend

**`app/dependencies/auth.py`**
- `get_current_user`: read `Authorization: Bearer <id_token>`, validate via `python-jose`
  against Cognito's JWKS (`https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`,
  cached in-process), check `aud` == client id, `iss`, `exp`. Extract `sub`, look up
  `User.cognito_sub`. 401 on any validation failure or missing user row.
- `get_current_user_optional`: same, but returns `None` when no `Authorization` header
  is present (already documented behaviour); a present-but-invalid token still 401s.

**`app/routers/auth.py` / `app/services/auth_service.py`**
- `sync_user` route: decode the bearer JWT directly (not via `get_current_user`, since no
  `User` row may exist yet) to get `sub`, `email`, `given_name`, `family_name`. Pass these
  into `auth_service.sync_user`.
- `auth_service.sync_user`: implement the upsert per its existing docstring — create on
  first login, update `first_name`/`last_name` on repeat logins, never raise on conflict.

**`app/services/user_service.py`**
- Implement `get_me`, `set_topics`, `get_topics` per their existing docstrings (currently
  blocking, since `users.router` depends on `get_current_user` which now works).

**Avatar upload**
- New migration: `User.avatar_s3_key: str | None`.
- `app/schemas/user.py`: `UserResponse` gains `avatar_url: str | None`, populated at
  response time as a presigned GET (1hr expiry) when `avatar_s3_key` is set, else `None`.
- `app/services/content_service.get_presigned_url`: implement per its existing docstring
  (boto3 `generate_presigned_url`) — shared by avatar GET and the existing audio-url route.
- New endpoint `POST /users/me/avatar-upload-url` → `{upload_url, key}`, a presigned PUT
  for `avatars/{user_id}/{uuid}.{ext}` (extension validated against `{jpg,jpeg,png,webp}`).
- New endpoint `PATCH /users/me` (or extend an existing user-mutation route) accepting
  `{avatar_s3_key}` to persist after the browser's direct S3 PUT succeeds.

## Frontend

**`lib/api/auth.ts`** (replace all four `not implemented` stubs)
- PKCE: generate `code_verifier`/`code_challenge`, store verifier in `sessionStorage`.
- `getCognitoLoginUrl()`: builds the Hosted UI `/login` authorize URL with
  `response_type=code`, `scope=email openid profile`, the PKCE challenge, and
  `redirect_uri=VITE_COGNITO_REDIRECT_URI`.
- `exchangeCode(code)`: POSTs directly to Cognito's `/oauth2/token` (standard public SPA
  client flow, no backend involvement) using the stored code_verifier.
- `syncUser(firstName, lastName)`: calls `POST /auth/sync` with the id_token attached.
- `signOut()`: clears stored tokens + `currentUser`, redirects to Cognito's `/logout`
  endpoint with `logout_uri=http://localhost:3000/`.

**New route `/auth/callback/+page.svelte`**: on mount, read `?code=`, call
`exchangeCode`, store tokens (`TOKEN_KEY` already defined in `client.ts`), call
`syncUser`, set `currentUser`, redirect to `/`.

**`lib/api/client.ts`**: `apiFetch` attaches `Authorization: Bearer <id_token>` from
storage when present.

**`NavBarAvatar.svelte`**: render `<img src={user.avatar_url}>` when set, else the
existing initials circle.

**`routes/settings/+page.svelte`**: replace the stub with a "Profile picture" file
input — on change, request an upload URL, PUT the file to S3, `PATCH /users/me` with
the returned key, refresh `currentUser`.

**`Navbar.svelte`**: "Log in" `NavLink` href becomes `getCognitoLoginUrl()`.

## Testing

- Backend: unit tests for JWT validation (valid / expired / bad signature / wrong
  audience) and `sync_user` upsert (create vs. update path).
- No automated end-to-end Cognito test — verified manually via the real local
  docker-compose flow before considering this done.

## Risks / known limitations

- Requires the user to run `terraform apply` and wire real values into `.env` /
  `docker-compose.yml` before any of this can be exercised end-to-end — implementation
  can proceed against the contract regardless, but manual verification is blocked until
  that's done.
- Backend needs AWS credentials in its container (e.g. `AWS_ACCESS_KEY_ID` /
  `AWS_SECRET_ACCESS_KEY` in `backend/.env`) for boto3 to sign presigned URLs locally —
  document this in `.env.example`.
