# LAMS-092 · README: architecture, setup steps, manual steps, screenshots

**Milestone:** [M13 – End to end and portfolio](README.md) · **Size:** M (2–5h) · **Delivers:** §19

**Depends on:** LAMS-090 (evidence and screenshots), LAMS-091 (coverage numbers), the manual-step notes from LAMS-086 – LAMS-089

## Goal

The root `README.md` replaces the Salesforce DX template. A reviewer can see what LAMS does, how it is built and which requirement each feature serves. Someone else can stand it up in their own org, including the steps that cannot live in source (§19 "Not in source").

## Build

**README outline** (root `README.md`; keep it scannable, and move long detail to `docs/` with a link)

| # | Section | Content |
| --- | --- | --- |
| 1 | Title + one line | "LAMS – Loan Application Management System on Salesforce: apply → approve → disburse → collect → close". CI badge from the LAMS-004 workflow |
| 2 | Demo | Link to the 5-minute video (LAMS-093) and 3 hero screenshots |
| 3 | The problem | 3–4 sentences from BRD §2, plus the four products from §5 |
| 4 | Feature map | Table: capability → where in LAMS → requirement, condensed from §21 (one row per capability, BR IDs kept) |
| 5 | Architecture | (a) Data model: the mermaid ER diagram from §10; (b) lifecycle image `docs/BRD/images/lifecycle.png`; (c) origination chain as a mermaid sequence diagram: Application Submitted → CreditBureauService → KycService → EligibilityService → ApplicationRouter (§14); (d) integrations table from §16; (e) AI and Data Cloud: the two agents, five actions, prompt template, and the Data Cloud steps from §17 |
| 6 | Design decisions | 5–8 bullets from the BRD appendix that show judgement: eligibility after the score, ApplicationRouter, Application_Key__c, org-default toggles, buffered logging, chunked SMS, owner assignment instead of a queue |
| 7 | Feature toggles | §12 table: field, default, what switching it off does |
| 8 | Repo layout | `force-app/`, `docs/BRD`, `docs/milestones`, `postman/`, `scripts/`, `.github/workflows` |
| 9 | Setup | Numbered steps (below) |
| 10 | Manual steps | Everything not in source (below) |
| 11 | Testing | Apex command, Jest command, coverage table link (`docs/COVERAGE.md`), AC list with where each is proven (`docs/AC-16-run.md`, Testing Center suite for AC-15) |
| 12 | Screenshots | Gallery (below) |
| 13 | Limitations | Developer Edition limits (§8 C1), mocks instead of real systems (A4), what was simulated or not supported in the org (Data Cloud / Agentforce differences, C4), Hindi in the agent |
| 14 | Out of scope / roadmap | §3 out-of-scope list |
| 15 | Licence and author | Licence (MIT, proposed), contact link |

**Setup steps** (section 9)

| # | Step |
| --- | --- |
| 1 | Prerequisites: Developer Edition with Agentforce and Data Cloud, Salesforce CLI (`sf`), Node (for Jest), Postman |
| 2 | `git clone`, `npm install` |
| 3 | `sf org login web --alias lams --set-default` |
| 4 | `sf project deploy start --manifest manifest/package.xml` (or each build-step manifest in order; list them) |
| 5 | Post-deploy settings: `sf apex run --file scripts/apex/<LAMS-020 script>` (use the actual file name) |
| 6 | Seed data: `sf data import tree --plan <LAMS-016 plan>` |
| 7 | Users and permission set group assignments (LAMS-029) |
| 8 | Fill External Credentials with the mock credentials; mock URLs from LAMS-006 |
| 9 | Schedule jobs: LoanOverdueScheduler (nightly), IntegrationRetryBatch (hourly); Daily Reminders flow active |
| 10 | Publish the portal; then do the manual steps below |

**Manual steps** (section 10). Each row says why it is manual and links to its detail doc.

| Area | Step | Detail |
| --- | --- | --- |
| Org features | Digital Experiences, Translation Workbench (Hindi), Business Hours "LAMS IST" if not deployed | LAMS-005 |
| Secrets | External Credential principals and values; CI auth URL as a GitHub secret | LAMS-040, LAMS-004 |
| Custom setting data | Org defaults via the script (data, not metadata) | LAMS-020 |
| Experience Cloud | Site publish, self-registration settings, guest and member settings not retrieved | LAMS-074 – LAMS-076 |
| Agentforce | Enable Agentforce; agent users and permission sets; topics and actions if the metadata does not deploy; Messaging channel, Omni-Channel flow, Embedded Service deployment, user verification; Operations queue presence | LAMS-086, LAMS-087 |
| Prompt templates | Activate after deploy | LAMS-085 |
| Data Cloud | Provisioning, data streams, DMO mappings, identity resolution, calculated insights, segments, Copy Field enrichment, data action and target | LAMS-088, LAMS-089, `docs/DATA_CLOUD_SETUP.md` (proposed) |
| Demo data | Clean-payer and early-risk seed scripts | LAMS-089 |

**Screenshots** (section 12, files in `docs/BRD/images/`, names proposed)

| File | Shows |
| --- | --- |
| `app-application-record.png` | Application record page with Dynamic Forms, documentChecklist, EMI |
| `portal-home.png`, `portal-my-loans.png` | Portal home with EMI calculator; My Loans with emiSchedule |
| `approval-history-hl.png` | Two-step approval on the Home Loan |
| `secured-review.png` | Secured Loan Review orchestration stages |
| `offer-letter.png` | OfferLetter PDF |
| `dashboard-origination.png`, `dashboard-portfolio.png`, `dashboard-integrations.png` | The three dashboards |
| `integration-log.png` | Integration logs with retries and Gave Up |
| `ac-15-guardrails.png` | Borrower Assistant declining and offering a hand-off |
| `officer-assistant-summary.png` | Application summary with risk flags |
| `data-cloud-profile.png`, `contact-pre-approved.png` | Unified profile; Contact with Repayment_Score__c and Pre_Approved__c |
| `lams-settings.png` | lamsSettings toggles |

## Steps

1. Draft the outline headings in `README.md`, replacing the DX template text completely.
2. Write the feature map from §21 and the toggles table from §12. Check every class, flow and field name against `force-app/`; the README must match what was built, not the plan.
3. Add the mermaid diagrams. Check that they render on GitHub (push to a branch and view it).
4. Write the setup steps and dry-run them. If possible, do this on a fresh Developer Edition, or at least redeploy to the current org from a clean clone, and fix every step that fails.
5. Collect the manual steps from the M10 – M12 item notes and `docs/DATA_CLOUD_SETUP.md`.
6. Take any missing screenshots with demo data only (no real names, PANs or emails). Compress them (≈ under 500 KB each) and link them.
7. Update the BRD if anything built differs from it (Definition of Done).
8. Commit: `docs(readme): architecture, setup, manual steps and screenshots [LAMS-092]`.

## Learn

- **The README is the portfolio:** reviewers spend minutes, not hours. Put the demo, the feature map and the architecture first, and setup detail lower down.
- **Manual steps are part of the design:** Salesforce has metadata that does not deploy cleanly (Data Cloud, some Agentforce and Experience Cloud settings). Writing them down honestly is what makes the project reproducible.
- **Traceability sells the work:** linking each feature to a BR ID shows it was built for a requirement, not to tick a box (§1 project objective).

## Done when

- [ ] `README.md` has every section in the outline; no DX template text remains
- [ ] The feature map covers every row of §21, and every name in it exists in `force-app/`
- [ ] The mermaid diagrams render on GitHub
- [ ] Setup steps were dry-run from a clean clone and work as written
- [ ] Every item from §19 "Not in source" is listed under manual steps with a link to its detail
- [ ] All screenshots in the table exist in `docs/BRD/images/` and are linked
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Org setup and DevOps (including "Not in source" and Secrets), §21 traceability, §10 ER diagram, §5 lifecycle, §12 toggles, §14 origination chain, §16 integrations, §17 Agentforce and Data Cloud, §2, §3, §8 C1, C4, A4, Appendix, §20 step 13
