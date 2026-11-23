# M01 – Org and repo

≈ 4h · 6 work items · Starts after: nothing

**Goal:** A Salesforce org and this repo are connected, with CI validating every push, so all later work is versioned and checked.

**Exit criteria:** a push to `main` passes CI.

## Work items

Tick items here; the linked file says what to build.

- [x] [LAMS-001](001-git-init-connect-github-repo-first-commit-and.md) · `git init`, connect GitHub repo, first commit and push, backlog checklist files · `S` — done 2026-11-21
- [x] [LAMS-002](002-sign-up-for-the-developer-edition-with.md) · Sign up for the Developer Edition with Agentforce and Data Cloud; confirm Experience Cloud, Orchestration, Messaging; record limits in `ORG_NOTES.md` · `S` — done 2026-11-23
- [ ] [LAMS-003](003-authorise-the-org-in-the-cli-set-default-org.md) · Authorise the org in the CLI; set default org and API version · `S`
- [ ] [LAMS-004](004-github-action-validate-only-deploy.md) · GitHub Action: validate-only deploy + RunLocalTests on every push (org auth URL as a repo secret) · `M`
- [ ] [LAMS-005](005-enable-digital-experiences-translation.md) · Enable Digital Experiences, Translation Workbench (Hindi), Business Hours "LAMS IST" · `S`
- [ ] [LAMS-006](006-create-public-mock-endpoints-beeceptor-postman.md) · Create public mock endpoints (Beeceptor/Postman) with success and failure responses · `M`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: a push to `main` passes CI.
- [ ] Deploys cleanly from source to the org
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._

- **Data Cloud licensed but not provisioned** (LAMS-002). Run *Data Cloud Setup → Get Started* well before M12; see [ORG_NOTES.md](ORG_NOTES.md#4-gaps-and-fallbacks).
- **Messaging capped at 10 conversations in total** (LAMS-002). Test the Borrower Assistant in preview; save real portal conversations for the demo (LAMS-087, LAMS-093).
- **CDC limited to 5 selected entities** (LAMS-002). LAMS-014 must stay at or under 5.
- Stray empty file `0` in the repo root (committed in 25f6f01, probably a shell redirect typo). Delete it in a `chore` commit.
