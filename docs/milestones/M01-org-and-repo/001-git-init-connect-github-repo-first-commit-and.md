# LAMS-001 · `git init`, connect GitHub repo, first commit and push, backlog checklist files

**Milestone:** [M01 – Org and repo](README.md) · **Size:** S (≤ 2h) · **Delivers:** BRD §19

**Depends on:** nothing (first item)

## Goal

The SFDX project, BRD and milestone checklists are under version control on GitHub, so every later change has a history and a backup.

## Build

| Item | Value |
| --- | --- |
| Local repo | `C:\Users\Suhas\Desktop\LAMS`, branch `main` |
| Remote | `LAMS` → `https://github.com/suhas45/LoanApplicationManagementSystem.git` |
| First commit | SFDX scaffold, `docs/BRD/`, `docs/milestones/`, `scripts/backlog/progress.py` |
| `.gitignore` | SFDX default: ignores `.sf/`, `.sfdx/`, `node_modules/`, `.env` |

## Steps

1. `git init` in the project folder and create the GitHub repository.
2. `git remote add LAMS <repo URL>`.
3. Check nothing secret is staged: `git status --porcelain --untracked-files=all`.
4. `git add -A`, commit, `git push -u LAMS main`.

## Learn

- A Salesforce DX project is plain files; git tracks metadata like any code.
- `.forceignore` (what the CLI skips) is different from `.gitignore` (what git skips).

## Done when

- [x] `git log` shows the first commit on `main`
- [x] The repo page on GitHub shows `docs/` and `force-app/`
- [x] `python scripts/backlog/progress.py` runs
- [x] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Org setup and DevOps
