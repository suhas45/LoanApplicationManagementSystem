# LAMS-093 · 5-minute demo video; make repo public

**Milestone:** [M13 – End to end and portfolio](README.md) · **Size:** S (≤ 2h) · **Delivers:** –

**Depends on:** LAMS-092 (README), LAMS-090 (the end-to-end run the video follows)

## Goal

A 5-minute video shows LAMS working end to end. The repository is then made public with no secrets in it or in its history. This finishes build step 13 (§20: "README with screenshots and a demo video") and makes the project ready to show.

## Build

**Video**

| Item | Value |
| --- | --- |
| Length | 5:00 or less |
| Format | 1080p screen recording with voice-over and captions; browser zoom about 110%; one browser profile per user, so the user switches are quick |
| Tool | Any screen recorder (for example OBS or Loom) |
| Hosting | YouTube (unlisted or public) or Loom; link it from the top of the README and from the GitHub repo's website field |
| Script | `docs/DEMO_SCRIPT.md` (proposed): the scene list below with the exact clicks and records to use |
| Data | Demo data only; prepare the records beforehand (from LAMS-090 and LAMS-089), and cut the waits |

**Scene list**

| Time | Scene | Shows | BR / AC |
| --- | --- | --- | --- |
| 0:00 – 0:20 | Hook | The problem in one sentence; the lifecycle image | §2, §5 |
| 0:20 – 0:45 | Architecture | ER diagram and feature map from the README; "every feature traces to a requirement" | §21 |
| 0:45 – 1:30 | Borrower applies | Portal home EMI calculator, Apply (Personal), Submit, upload documents; cut to the score and eligibility arriving; Integration log rows | BR-04, BR-10 – BR-12, BR-17 |
| 1:30 – 2:00 | Auto-approve | Officer verifies the last document → Approved instantly; offer letter PDF | AC-01 |
| 2:00 – 2:45 | Home Loan | Secured Loan Review stages; Credit Manager reduces the amount; waits for Credit Head; two-step approval history | BR-20, BR-25, AC-03 |
| 2:45 – 3:25 | Servicing | Disburse → EMI schedule; Postman payment callback, the same reference again is rejected; prepayment quote → loan Closed; closure letter | BR-37, BR-41, BR-44, AC-10 |
| 3:25 – 4:05 | AI | Borrower Assistant: status, missing documents, then "approve my loan" → declines and offers a hand-off; Loan Officer Assistant summary with risk flags | BR-75 – BR-77, AC-15 |
| 4:05 – 4:30 | Data Cloud | Unified profile; the borrower's Contact with Repayment_Score__c and Pre_Approved__c; it joins the top-up campaign (M14); early-risk Task | BR-78, BR-88 |
| 4:30 – 4:50 | Control | lamsSettings: switch auto-approve off and show the next application going to the Credit Managers; dashboards | BR-79, BR-80, AC-02, BR-62 – BR-64 |
| 4:50 – 5:00 | Close | Coverage figure, CI badge, repo URL | NFR-10 |

**Make the repo public: checklist**

| # | Check | How |
| --- | --- | --- |
| 1 | No secrets in the current tree | Search for `force://`, `sfdxAuthUrl`, `client_secret`, `clientSecret`, `password`, `Bearer `, `token`. Check `postman/` environment files (export them with secret values blank) and [ORG_NOTES.md](../M01-org-and-repo/ORG_NOTES.md) (no passwords, security tokens or personal usernames) |
| 2 | No secrets in history | Run a secret scanner over all commits, for example `gitleaks` (`gitleaks git .` in current versions, or `gitleaks detect --source . --log-opts="--all"` in older ones), or `git log -p --all` piped to the same search |
| 3 | If anything was ever committed | **Rotate it first**: revoke the CI auth URL (log out the CLI session / reset the connected or external client app) and regenerate client secrets and External Credential values. Then remove it from history (`git filter-repo`) or publish a fresh repository |
| 4 | Ignored files | `.sf/`, `.sfdx/`, `.env`, `node_modules/`, `coverage/`, `test-results/` are in `.gitignore` and not tracked (`git ls-files` shows none of them) |
| 5 | Personal data | Seed data, screenshots and the video use fake names, PANs, phone numbers and emails only. No real org usernames or emails in screenshots |
| 6 | CI secret safety | The CI auth URL stays a GitHub Actions secret. The workflow uses `pull_request` (fork PRs get no secrets), never `pull_request_target` with a checkout of PR code. Require approval for workflows from outside contributors |
| 7 | GitHub protections | Turn on secret scanning and push protection, Dependabot alerts, and branch protection on `main` (CI must pass) |
| 8 | Presentation | Repo description, topics (salesforce, apex, lwc, agentforce, data-cloud, experience-cloud), website field set to the video, `LICENSE` file (MIT, proposed) |
| 9 | Go public | Settings → General → Danger Zone → Change visibility → Public |
| 10 | Verify as a stranger | In a private window: the README renders, images and diagrams load, the video plays, links to the BRD and milestones work |

## Steps

1. Write `docs/DEMO_SCRIPT.md` from the scene list; prepare the records and browser profiles; reset any toggles you will flip.
2. Do one rehearsal with a timer; cut whatever pushes past 5:00.
3. Record, edit out the waits, add captions, and upload. Put the link in the README.
4. Work through checklist items 1–8. Fix anything you find, and rotate before any history rewrite.
5. Commit: `docs(portfolio): demo video link, demo script and licence [LAMS-093]`, and push to `main` (CI green).
6. Item 9: make the repository public. Then item 10.
7. Write the M13 devlog entry and close the milestone.

## Learn

- **Making a repo public exposes its whole history**, not just the latest commit. A secret deleted in a later commit is still public. Rotation is the only real fix; a history rewrite is cleanup.
- **The demo follows the requirements:** each scene maps to BR or AC IDs, so the video doubles as evidence that the system meets the BRD.
- **Fork pull requests and secrets:** GitHub withholds secrets from `pull_request` runs triggered by forks; `pull_request_target` does not, which is why it is risky on a public repo.

## Done when

- [ ] The video is 5:00 or shorter, covers every scene in the list, and is linked from the README
- [ ] A secret scan over all commits finds nothing (or every finding was rotated and removed)
- [ ] `git ls-files` shows no `.sf/`, `.sfdx/`, `.env` or test-result files
- [ ] Secret scanning, push protection and branch protection on `main` are on
- [ ] The repository is public, and the README, images and video work in a private browser window
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §20 step 13, §19 Source control and deployment (Secrets row, CI), §21 traceability, §9 acceptance criteria used in the scenes, NFR-06
