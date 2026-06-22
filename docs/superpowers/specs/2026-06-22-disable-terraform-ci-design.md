# Disable Automatic Terraform CI — Design Spec

## Background

`.github/workflows/terraform.yml` runs a `Plan` job on every PR touching `infrastructure/**` and an `Apply` job on every push to `main` touching the same paths. Both require a `TF_API_TOKEN` secret (a Terraform Cloud token) to authenticate `terraform init` against the `exeaws26-prod` HCP Terraform workspace. That secret has never been set (`gh secret list` returns nothing), so `Plan` has been hard-failing at the `terraform init` step on every infra PR — including PR #12, which carries the GHCR registry-standardisation work from this session.

The team is currently prototyping locally only — no AWS account/Terraform Cloud workspace has actually been applied to, and there's no near-term plan to deploy. The failing check is noise unrelated to the correctness of any given infra PR's content, and there is no real backend to plan/apply against yet anyway.

## Decision

Switch `terraform.yml`'s trigger from automatic (`pull_request` + `push`) to **manual only** (`workflow_dispatch`). This is the only change. The `plan` and `apply` job bodies, their `if` conditions, and the `TF_API_TOKEN` wiring are left untouched — they'll work exactly as before once someone runs the workflow manually with a real token configured.

**Why manual trigger over the alternatives considered:**
- Renaming the file to disable it (`terraform.yml.disabled`) achieves the same practical effect but makes the workflow invisible in the Actions tab — harder for a teammate to discover it exists and is just waiting for a token.
- A repo-variable gate (`if: vars.INFRA_DEPLOY_ENABLED == 'true'`) would let the automatic triggers stay wired and show a clean "skipped" status, but that's more machinery than needed for "we're not deploying yet" — YAGNI.
- `workflow_dispatch` is the smallest diff, keeps the workflow visible and runnable on demand, and is trivially reversible (restore the two trigger blocks) once Terraform Cloud is actually set up.

## Change

`.github/workflows/terraform.yml`, the `on:` block:

```yaml
on:
  workflow_dispatch:
```

replaces:

```yaml
on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']
```

Everything else in the file (concurrency group, both jobs, their `if` conditions referencing `github.event_name`, the `TF_API_TOKEN` env vars) is unchanged. Note: the `plan` job's `if: github.event_name == 'pull_request'` and the `apply` job's `if: github.event_name == 'push' && ...` will now never be true under `workflow_dispatch` triggering — so as written, manually running the workflow would run neither job. This needs a follow-up adjustment so a manual run can still choose to do something (see below), otherwise `workflow_dispatch` is a trigger with no reachable job.

**Resolving that:** add a `workflow_dispatch` input (e.g. `action: choice` between `plan` and `apply`, default `plan`) and change each job's `if` to check `github.event.inputs.action == 'plan'` / `'apply'` instead of `github.event_name`. This keeps a single workflow file usable for both manual operations once someone is ready to actually point it at real infrastructure.

## Out of scope

- Setting up `TF_API_TOKEN` or the Terraform Cloud workspace itself — that's a separate, later task for whenever real deployment starts.
- PR #12 / the GHCR registry-standardisation work — unaffected by this change, can be merged independently once this lands (the failing check will simply disappear since there's no automatic trigger left to fail).
