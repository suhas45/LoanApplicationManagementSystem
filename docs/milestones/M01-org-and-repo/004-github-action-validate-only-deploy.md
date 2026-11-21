# LAMS-004 · GitHub Action: validate-only deploy + RunLocalTests on every push (org auth URL as a repo secret)

**Milestone:** [M01 – Org and repo](README.md) · **Size:** M (2–5h) · **Delivers:** §19

**Depends on:** LAMS-001 (GitHub repo), LAMS-003 (`Lams` authorised in the CLI)

## Goal

Every push and every pull request to `main` is checked by a validate-only deploy against the org, so broken metadata or failing tests never reach `main` (§19 CI row; build step 1 is done when this passes on an empty project). From the first Apex class onward the same job runs all local tests, which backs NFR-10.

## Build

**Repo secret**

| Name | Value |
| --- | --- |
| `SFDX_AUTH_URL` (proposed name) | The `sfdxAuthUrl` (`force://…`) of `Lams`, from `sf org display --verbose --json` |

**File `.github/workflows/validate.yml`**

| Setting | Value |
| --- | --- |
| Name | `Validate` (job id `validate`; this is the status check name) |
| Triggers | `push` on all branches, `pull_request` to `main`, `workflow_dispatch` |
| Runner | `ubuntu-latest`, timeout 30 min |
| Node | `lts/*` via `actions/setup-node` |
| CLI | `npm install --global @salesforce/cli` |
| Auth | `sf org login sfdx-url` from the secret, alias `lams-ci` |
| Deploy, no Apex yet | `sf project deploy start --dry-run --test-level NoTestRun` |
| Deploy, Apex present | `sf project deploy validate --test-level RunLocalTests` (the BRD §19 command) |
| Empty project | If `force-app` has no files yet (git does not store empty folders), log a notice and pass |

```yaml
name: Validate

on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: validate-${{ github.ref }}
  cancel-in-progress: true

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'

      - name: Install Salesforce CLI
        run: npm install --global @salesforce/cli

      - name: Authenticate org
        env:
          SFDX_AUTH_URL: ${{ secrets.SFDX_AUTH_URL }}
        run: |
          echo "$SFDX_AUTH_URL" > ./authurl.txt
          sf org login sfdx-url --sfdx-url-file ./authurl.txt --alias lams-ci --set-default
          rm ./authurl.txt
          sf data query --query "SELECT Name FROM Organization" --target-org lams-ci

      - name: Validate deploy
        run: |
          if [ -z "$(find force-app -type f ! -name '.gitkeep' 2>/dev/null | head -1)" ]; then
            echo "::notice::force-app has no metadata yet - nothing to validate"
            exit 0
          fi
          if ls force-app/main/default/classes/*.cls >/dev/null 2>&1; then
            sf project deploy validate --source-dir force-app --test-level RunLocalTests --wait 30 --target-org lams-ci
          else
            sf project deploy start --dry-run --source-dir force-app --test-level NoTestRun --wait 30 --target-org lams-ci
          fi
```

The `if ls … *.cls` switch means you never edit the workflow when LAMS-019 adds the first class (FeatureToggle): from then on every run executes RunLocalTests.

**Branch protection (proposed):** GitHub → Settings → Branches → rule for `main`: require a pull request and the `validate` status check.

## Steps

1. Branch: `git checkout -b chore/LAMS-004-ci-validate`.
2. Get the auth URL and store it as a secret without writing it to disk (PowerShell, GitHub CLI logged in):
   `(sf org display --target-org Lams --verbose --json | ConvertFrom-Json).result.sfdxAuthUrl | gh secret set SFDX_AUTH_URL`
   Or copy it into GitHub → Settings → Secrets and variables → Actions → *New repository secret*.
3. Create `.github/workflows/validate.yml` with the content above.
4. Commit and push: `ci(github): validate-only deploy workflow [LAMS-004]`, then `git push -u LAMS chore/LAMS-004-ci-validate`.
5. Open the *Actions* tab; the run must be green and log the empty-project notice.
6. Negative test: on the branch, add a broken file (for example `force-app/main/default/objects/Broken__c/Broken__c.object-meta.xml` containing `<CustomObject>` with no closing tag), push, and check that the run fails. Delete the file and push again; the run is green.
7. Open a pull request to `main`, merge when green, and check the run on `main` (M01 exit criterion).
8. Add the branch protection rule.

## Learn

- **SFDX auth URL** = a refresh token in URL form; anyone holding it can act as your user in the org. Keep it only in GitHub secrets, never in the repo or logs. If CI auth starts failing (password reset, token revoked, `sf org logout`), regenerate it and update the secret.
- **Do not print `sf org display` in CI:** it shows the access token, and GitHub only masks values that are secrets themselves.
- **Validate vs dry-run:** `deploy validate` is a check-only deploy that requires a test level that runs tests and returns a job ID that `sf project deploy quick` can later deploy without re-running tests; `deploy start --dry-run` is also check-only and accepts `NoTestRun`. If your org rejects `NoTestRun`, use `RunLocalTests`, which passes when there are no tests.
- Deployments to one org are queued, so two branches pushing at once just wait; the `concurrency` group only cancels older runs of the same branch.

## Done when

- [ ] Secret `SFDX_AUTH_URL` exists in the repo settings and appears nowhere in git history (`git log -p | Select-String force://` finds nothing)
- [ ] `.github/workflows/validate.yml` is on `main`
- [ ] A push to a feature branch and the PR to `main` each show a green `validate` check
- [ ] The broken-file push failed the check, and the fix made it green again
- [ ] A push to `main` passes CI (M01 exit criterion)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Source control and deployment (CI, Secrets rows); §20 step 1 done-when; NFR-10
