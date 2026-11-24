# LAMS-004 · Learning notes: CI with GitHub Actions (dropped)

**Date:** 2026-11-24 · **Milestone:** M01 – Org and repo · **Spec:** [004-github-action-validate-only-deploy.md](../milestones/M01-org-and-repo/004-github-action-validate-only-deploy.md) · **Status:** dropped

## 1. What the item was

**CI (continuous integration)** means a server automatically checks every push. For LAMS that would have been a GitHub Action that, on each push:

1. Starts a fresh Linux machine on GitHub.
2. Installs the Salesforce CLI.
3. Logs in to the `Lams` org with an **SFDX auth URL** stored as a GitHub secret.
4. Runs a **check-only deploy**: Salesforce validates the metadata and runs tests, then rolls everything back.
5. Shows ✅ or ❌ on the commit.

## 2. Why it was dropped

The goal is a working project with code stored in GitHub. CI is a safety net on top of that, not a requirement:

- Code gets to GitHub with a plain `git push`.
- Each work item is deployed to `Lams` from the CLI anyway, so errors show up there.
- Setup needs a GitHub CLI login and a stored org token, which is extra work and one more secret to look after.

## 3. What was kept

The finished workflow is saved at [ci-validate.yml](../milestones/M01-org-and-repo/ci-validate.yml). GitHub only runs workflows inside `.github/workflows/`, so it does nothing where it is. To turn CI on later:

1. `gh auth login`
2. `(sf org display --target-org Lams --verbose --json | ConvertFrom-Json).result.sfdxAuthUrl | gh secret set SFDX_AUTH_URL` (pipes the token straight into GitHub, never shown on screen)
3. Copy `ci-validate.yml` to `.github/workflows/validate.yml`, commit, push.

## 4. What replaces CI in the workflow

Before pushing each work item, run from the CLI:

```bash
sf project deploy start --target-org Lams            # deploy, see errors
sf apex run test --test-level RunLocalTests --target-org Lams --wait 10   # once Apex exists
```

## 5. Concepts worth remembering

- **SFDX auth URL** (`force://…`) is a refresh token in URL form. Anyone who has it can act as you in the org. Never commit it, print it or paste it.
- **Check-only deploy:** `sf project deploy start --dry-run` or `sf project deploy validate` validates without saving. That's useful locally too, when you want to know if something will deploy.
- **Dropping work is a valid decision.** Record it (struck-through item, reason, date) so later items don't wait on something that will never come.

## 6. What changed in the repo

| File | Change |
| --- | --- |
| `docs/milestones/M01-org-and-repo/README.md` | LAMS-004 struck through as dropped; exit criteria now "code is pushed to `main`"; parking-lot note for CI mentions in LAMS-091/092/093 |
| `docs/milestones/README.md` | M01 exit criterion, workflow step 4 and Definition of Done no longer require CI |
| `docs/milestones/M01-org-and-repo/ci-validate.yml` | The parked workflow |
