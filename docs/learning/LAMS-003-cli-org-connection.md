# LAMS-003 · Learning notes: connecting the CLI to the org

**Date:** 2026-11-23 · **Milestone:** M01 – Org and repo · **Spec:** [003-authorise-the-org-in-the-cli-set-default-org.md](../milestones/M01-org-and-repo/003-authorise-the-org-in-the-cli-set-default-org.md) · **Output:** [ORG_NOTES.md](../milestones/M01-org-and-repo/ORG_NOTES.md) (Org section)

## 1. What this work item was about

Every later `deploy`, `retrieve` and `data` command depends on the Salesforce CLI pointing at the **right org** with the **right API version**. This item makes sure of that once, so you never need extra flags or worry that a command went to the wrong org.

The org was already authorised as `Lams`, so the work was checking, plus updating an old CLI.

## 2. What changed

| Where | Change |
| --- | --- |
| Your machine | CLI updated from 2.146.3 to **2.159.7** with `sf update stable` |
| `ORG_NOTES.md` | Org section now records login URL, API version reasoning, CLI version and how the CLI is installed |
| `docs/milestones/M01-org-and-repo/README.md` | LAMS-003 ticked |
| `sfdx-project.json` | **No change needed**, because `sourceApiVersion` 68.0 already matched the org |

## 3. The checks, and what each one proves

| Command | What it proves | Result |
| --- | --- | --- |
| `sf --version` | Which CLI and Node version runs | 2.159.7, Node 26.13.0 |
| `sf org list` | Org is authorised and the refresh token still works | `Lams` Connected, marked `(U)` = default |
| `sf config list` | Where the default org is set | `target-org = Lams`, Location **Local** |
| `sf org display --target-org Lams` | Org's API version | 68.0 |
| `sf data query --query "SELECT Name, OrganizationType, InstanceName FROM Organization"` | End-to-end smoke test: auth, API call, SOQL | Developer Edition, USA840 |
| `git status --ignored` | `.sf/` and `.sfdx/` stay out of git | Both ignored, none tracked |
| `sf project deploy start --dry-run` | The deploy path reaches the org | `NothingToDeploy`, expected because `force-app` is still empty |

## 4. What went wrong, and what it teaches

**The update didn't seem to work.** `npm install --global @salesforce/cli` reported success, but `sf --version` still said 2.146.3.

**Why:** there were two CLIs on PATH.

```
Get-Command sf -All
C:\Program Files\sf\bin\sf.cmd          <- Windows installer (first on PATH, so this one runs)
C:\Users\Suhas\AppData\Roaming\npm\sf.cmd  <- npm copy (never reached)
```

Windows runs the first match on PATH. The installer version updates itself into `%LOCALAPPDATA%\sf\client\<version>\` when you run `sf update`. npm installs a completely separate copy.

**Fix:** `sf update stable` updated the copy that actually runs, then `npm uninstall --global @salesforce/cli` removed the duplicate.

**Rule:** update the CLI the same way you installed it. For the Windows installer that's `sf update`; for npm it's `npm install -g`. When a version doesn't change after an update, run `Get-Command sf -All` (PowerShell) or `where sf` (cmd).

**The `EPERM` error during the update** came from the updater trying to delete the old version's `node.exe` while something (usually VS Code's Salesforce extension) was still using it. The new version installed fine; the old folder just stays behind. Restarting VS Code and running `sf update` again cleans it up.

## 5. Salesforce concepts practised

- **Alias vs username.** Commands accept either. An alias (`Lams`) keeps usernames out of scripts and docs, and lets you re-point the alias later without editing anything.
- **Local vs global config.** `sf config set target-org=Lams` writes to `.sf/config.json` in this project (Local). Adding `--global` writes to your home folder and affects every project. Local is safer here, because client sandboxes are authorised on the same machine.
- **Where auth lives.** The refresh token is stored in your home folder (`~/.sfdx`), never in the project. That's why the repo can be public, and why CI needs its own credential (an auth URL as a GitHub secret, in LAMS-004).
- **`sourceApiVersion` vs `org-api-version`.**
  - `sourceApiVersion` (in `sfdx-project.json`) sets the **metadata format** of your source files.
  - `org-api-version` (CLI config) forces the **API version the CLI calls**. When it's unset, the CLI uses the org's own version, which is what we want.
  - Keep both at or below the org's version. During release previews a new CLI can expect a newer API than your org has; that's when you'd set `org-api-version`.
- **`sf org display` prints an access token.** Never paste its output anywhere. Use `--json` and pick out only the fields you need, as done here.

## 6. Still to do by hand

- Optional: restart VS Code, then run `sf update` once more to remove the old 2.146.3 folder.
- Check the VS Code status bar shows `Lams` as the default org.
