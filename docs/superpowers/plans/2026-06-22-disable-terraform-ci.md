# Disable Automatic Terraform CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `terraform.yml` from automatically running (and hard-failing, since no `TF_API_TOKEN` exists yet) on every infra PR/push to main, while keeping it available to run manually once Terraform Cloud is actually set up.

**Architecture:** Change the workflow's trigger from `pull_request`/`push` to `workflow_dispatch` with a `plan`/`apply` choice input, and switch each job's `if` condition to check that input instead of `github.event_name`. Also fix the `plan` job's "Post plan as PR comment" step, which currently relies on `context.issue.number` (only present on `pull_request` events) — under `workflow_dispatch` there's no associated PR, so that step would always fail; replace it with writing to the job's step summary instead, which works under any trigger.

**Tech Stack:** GitHub Actions YAML. No new tooling.

See `docs/superpowers/specs/2026-06-22-disable-terraform-ci-design.md` for the full design rationale.

---

## File Map

| Action | Path |
|---|---|
| Modify | `.github/workflows/terraform.yml` |

There's no way to actually run this GitHub Actions workflow locally to verify it executes correctly (no `act` or similar installed, and it requires Terraform Cloud credentials regardless). Verification in this plan is: (1) confirm the YAML is syntactically valid via `python3` + `pyyaml` (confirmed available in this environment), and (2) confirm the trigger and `if` conditions read correctly by inspection/grep. Real end-to-end verification happens the first time someone actually clicks "Run workflow" once a token exists — out of scope here.

---

### Task 1: Switch `terraform.yml` to manual-only trigger

**Files:**
- Modify: `.github/workflows/terraform.yml`

Current content of `.github/workflows/terraform.yml`:

```yaml
name: Terraform

on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

concurrency:
  group: terraform-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true

permissions: {}

jobs:
  plan:
    name: Plan
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      pull-requests: write
    env:
      TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: '1.9'
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -input=false
        working-directory: infrastructure
        continue-on-error: true

      - name: Post plan as PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan \`${{ steps.plan.outcome }}\`
            <details><summary>Show Plan</summary>

            \`\`\`terraform
            ${{ steps.plan.outputs.stdout }}
            \`\`\`

            </details>`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

      - name: Fail if plan failed
        if: steps.plan.outcome == 'failure'
        run: exit 1

  apply:
    name: Apply
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
    env:
      TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: '1.9'
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure

      - name: Terraform Apply
        run: terraform apply -auto-approve -input=false
        working-directory: infrastructure
```

- [ ] **Step 1: Replace the file contents**

  Replace the entire file with:

  ```yaml
  name: Terraform

  on:
    workflow_dispatch:
      inputs:
        action:
          description: 'Terraform action to run'
          type: choice
          options:
            - plan
            - apply
          default: plan

  concurrency:
    group: terraform-${{ github.head_ref || github.ref_name }}
    cancel-in-progress: true

  permissions: {}

  jobs:
    plan:
      name: Plan
      runs-on: ubuntu-latest
      if: github.event.inputs.action == 'plan'
      permissions:
        contents: read
        pull-requests: write
      env:
        TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
      steps:
        - uses: actions/checkout@v4

        - uses: hashicorp/setup-terraform@v3
          with:
            terraform_version: '1.9'
            cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

        - name: Terraform Init
          run: terraform init
          working-directory: infrastructure

        - name: Terraform Plan
          id: plan
          run: terraform plan -no-color -input=false
          working-directory: infrastructure
          continue-on-error: true

        - name: Post plan to job summary
          run: |
            echo "#### Terraform Plan \`${{ steps.plan.outcome }}\`" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo '```terraform' >> "$GITHUB_STEP_SUMMARY"
            echo "${{ steps.plan.outputs.stdout }}" >> "$GITHUB_STEP_SUMMARY"
            echo '```' >> "$GITHUB_STEP_SUMMARY"

        - name: Fail if plan failed
          if: steps.plan.outcome == 'failure'
          run: exit 1

    apply:
      name: Apply
      runs-on: ubuntu-latest
      if: github.event.inputs.action == 'apply'
      permissions:
        contents: read
      env:
        TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
      steps:
        - uses: actions/checkout@v4

        - uses: hashicorp/setup-terraform@v3
          with:
            terraform_version: '1.9'
            cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

        - name: Terraform Init
          run: terraform init
          working-directory: infrastructure

        - name: Terraform Apply
          run: terraform apply -auto-approve -input=false
          working-directory: infrastructure
  ```

  Note what changed from the original and why:
  - `on:` block: `pull_request`/`push` triggers replaced with `workflow_dispatch` + a `plan`/`apply` choice input (default `plan`), per the approved design — this is what makes the workflow manual-only.
  - `plan` job's `if`: `github.event_name == 'pull_request'` → `github.event.inputs.action == 'plan'` (there's no `pull_request` event anymore to check against).
  - `apply` job's `if`: `github.event_name == 'push' && github.ref == 'refs/heads/main'` → `github.event.inputs.action == 'apply'` (same reasoning; there's no `push` event to check, and no branch restriction needed since this now only ever runs when someone deliberately dispatches it).
  - `plan` job's PR-comment step renamed to "Post plan to job summary" and rewritten to append to `$GITHUB_STEP_SUMMARY` via plain shell, instead of calling `github.rest.issues.createComment` with `context.issue.number`. Under `workflow_dispatch` there is no associated pull request, so `context.issue.number` would be `undefined` and the original step would fail every run. The step summary is visible on the workflow run page regardless of trigger type, so this preserves the "see the plan output" behavior without depending on a PR existing.
  - Everything else (concurrency group, `permissions: {}`, both jobs' `permissions`, `TF_API_TOKEN` wiring, Terraform Init/Plan/Apply steps) is unchanged.

- [ ] **Step 2: Validate YAML syntax**

  ```bash
  python3 -c "import yaml; yaml.safe_load(open('.github/workflows/terraform.yml'))" && echo "valid YAML"
  ```
  Expected: `valid YAML` with no exception/traceback.

- [ ] **Step 3: Verify the trigger and conditions by inspection**

  ```bash
  grep -n "workflow_dispatch\|pull_request\|github.event_name\|github.event.inputs.action\|GITHUB_STEP_SUMMARY\|context.issue" .github/workflows/terraform.yml
  ```
  Expected output: shows `workflow_dispatch:` present, zero matches for `pull_request` or `github.event_name`, two matches for `github.event.inputs.action` (one per job's `if`), `GITHUB_STEP_SUMMARY` present (multiple lines in the new step), and zero matches for `context.issue`.

- [ ] **Step 4: Commit**

  ```bash
  git add .github/workflows/terraform.yml
  git commit -m "ci: make terraform workflow manual-dispatch only

  No Terraform Cloud token is configured yet and the team is prototyping
  locally with no real AWS deployment target, so automatic plan/apply on
  every infra PR/push was just failing noise. Switch to workflow_dispatch
  with a plan/apply choice input; restore automatic triggers once
  TF_API_TOKEN and a real deployment are in place."
  ```

- [ ] **Step 5: Push**

  ```bash
  git push origin HEAD
  ```
  Expected: push succeeds. This lands on whatever branch is currently checked out (confirm with `git branch --show-current` before pushing — at the time this plan was written that was `dev`, already tracking origin).
