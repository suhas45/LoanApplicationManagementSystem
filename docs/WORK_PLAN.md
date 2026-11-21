# LAMS – Work Plan and Tracking

How the build in [LAMS_BRD_v2.md](LAMS_BRD_v2.md) is divided, tracked and finished. Personal project, one developer, no Jira.

## 1. Tracking setup

**Tool: Markdown checklist files in the repo** — [docs/backlog/](backlog/README.md). No external tool, no login.

| File | Used for |
| --- | --- |
| [backlog/README.md](backlog/README.md) | Index of the 13 milestones, status markers, how to update |
| `backlog/M01-…md` – `M13-…md` | One file per milestone: its work items as tick boxes, plus the milestone exit checklist |
| [DEVLOG.md](DEVLOG.md) | Short dated notes when a milestone closes |
| `python scripts/backlog/progress.py` | Prints % done per milestone and overall |

Git history is the audit trail: each commit that ticks a box records when the item was done. §4 below is the master list the checklist files were generated from; if they ever differ, the checklist files win.

Size: `S` (≤ 2h) · `M` (2–5h) · `L` (5–10h). Switching to GitHub Issues later is possible with `scripts/github/create_backlog.py`.

## 2. How work is divided

Three levels, no more:

1. **Milestone** = one build phase from BRD §20 (M01 – M13). Ends with a demo-able result and named acceptance criteria.
2. **Work item** = one tick box, 1–10 hours, one deployable slice (for example "CreditBureauService + tests"). Anything bigger than `L` is split.
3. **Definition of Done** (§5) = the checks every item passes before its box is ticked.

Rules:

- Build in milestone order; inside a milestone, follow the dependency notes.
- **Tests ship with the class**, in the same work item — never a "write tests later" item.
- Every work item names the BR / AC IDs it delivers, so §21 of the BRD stays true.
- New ideas or bugs found mid-work go under **Parking lot** in the milestone file. Don't do them in the current branch.
- **WIP limit: 1 item In Progress, 1 in Review.** Finish before starting.

## 3. Workflow per work item

1. In the milestone file, add `**(in progress)**` after the item. Create a branch: `feat/LAMS-0606-credit-bureau` (or `fix/…`, `chore/…`).
2. Build in the org, retrieve to source (`sf project retrieve start`) or write source and deploy.
3. Commit with the item ID: `feat(apex): CreditBureauService with retry [LAMS-0606]`.
4. Run the self-review checklist (§6). Push; CI runs a validate-only deploy and the local tests. Fix until green.
5. Merge to `main` (a PR is optional when working alone, but gives a place for screenshots).
6. Tick the box, replace `(in progress)` with `— done YYYY-MM-DD`, and commit: `chore(backlog): done LAMS-0606`.

Found a bug or idea mid-work? Add it under **Parking lot** at the bottom of that milestone file; don't do it in the current branch.

**Milestone close:** demo the acceptance criteria, note the result in `docs/DEVLOG.md` (date, what works, what was learned, one screenshot), and update the BRD if the design changed.

**Weekly rhythm (suggested):** Sunday 20 min – run `progress.py`, pick the next 3–4 items. Each session – one item. Friday – update the devlog.

## 4. Backlog

IDs: `LAMS-MMNN` (MM = milestone). Size is a rough single-developer estimate.

### M01 – Org and repo (≈ 4h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0101 | `git init`, connect GitHub repo, first commit and push, backlog checklist files | S | §19 |
| LAMS-0102 | Sign up for the Developer Edition with Agentforce and Data Cloud; confirm Experience Cloud, Orchestration, Messaging; record limits in `docs/ORG_NOTES.md` | S | C1, D1 |
| LAMS-0103 | Authorise the org in the CLI; set default org and API version | S | §19 |
| LAMS-0104 | GitHub Action: validate-only deploy + RunLocalTests on every push (org auth URL as a repo secret) | M | §19 |
| LAMS-0105 | Enable Digital Experiences, Translation Workbench (Hindi), Business Hours "LAMS IST" | S | §19 |
| LAMS-0106 | Create public mock endpoints (Beeceptor/Postman) with success and failure responses | M | D2, §16 |

**Exit:** a push to `main` passes CI.

### M02 – Data model (≈ 12h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0201 | Loan_Product__c + Product_Document__c | M | §10.2 |
| LAMS-0202 | Contact custom fields + PAN Duplicate Rule | S | BR-02 |
| LAMS-0203 | Loan_Application__c fields, 4 record types, picklists | L | §10.3 |
| LAMS-0204 | Application_Document__c, roll-ups, Docs_Complete__c | M | BR-19 |
| LAMS-0205 | Formulas: Risk_Grade, EMI, EMI_To_Income, LTV | M | BR-14, BR-39 |
| LAMS-0206 | Loan__c with Application_Key__c, encrypted Payout_Account__c | M | §10.5 |
| LAMS-0207 | EMI_Instalment__c, Payment__c, loan roll-ups and formulas | M | §10.6, §10.7 |
| LAMS-0208 | Case record type + fields, Integration_Log__c, Loan_Event__e, CDC | M | §10.8 – §10.10 |
| LAMS-0209 | Page layouts, Lightning record pages (Dynamic Forms), LAMS app, tabs | L | BR-05 |
| LAMS-0210 | Seed data plans: 4 products, checklists, demo borrowers | S | §5 |

**Exit:** seed data loads; AC-09 EMI checks by hand on a record (₹8,979).

### M03 – Configuration (≈ 6h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0301 | LAMS_Settings__c fields | S | §12 |
| LAMS-0302 | Integration_Setting__mdt + 5 records | S | BR-82 |
| LAMS-0303 | FeatureToggle class + tests | S | BR-79 |
| LAMS-0304 | Post-deploy script that sets settings defaults | S | §19 |
| LAMS-0305 | Custom labels (first set) + Hindi translations | M | BR-54 |

**Exit:** script runs; a toggle is readable from Apex and from a Flow.

### M04 – Security (≈ 10h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0401 | Role hierarchy | S | §11 |
| LAMS-0402 | Profiles: LAMS Internal User, LAMS Borrower, Integration | M | §11 |
| LAMS-0403 | 8 permission sets + 3 custom permissions | L | §11 |
| LAMS-0404 | Permission set groups + muting set | S | BR-74 |
| LAMS-0405 | OWDs + criteria sharing rule | S | BR-70 |
| LAMS-0406 | FLS (PAN, income, score), View Encrypted Data | S | BR-71, BR-72 |
| LAMS-0407 | Field History Tracking | S | BR-73 |
| LAMS-0408 | Test users and group assignments | S | §19 |
| LAMS-0409 | lamsSettings LWC + LamsSettingsController + tests | M | BR-74 |

**Exit:** AC-14 passes logged in as an Operations Officer.

### M05 – Validation rules (≈ 4h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0501 | Loan_Application__c rules (10) | M | §13.1 |
| LAMS-0502 | Application_Document__c, EMI_Instalment__c, Payment__c rules | S | §13.1 |
| LAMS-0503 | Negative tests for every rule | S | NFR-10 |

### M06 – Origination (≈ 18h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0601 | emiCalculator LWC + Jest tests | M | BR-04 |
| LAMS-0602 | New Loan Application screen flow | L | BR-01, BR-04 |
| LAMS-0603 | LoanEventPublisher + tests | S | BR-68 |
| LAMS-0604 | OwnerAssignmentService + tests | M | BR-07, BR-33 |
| LAMS-0605 | Application Submitted flow | M | BR-09, BR-16 |
| LAMS-0606 | IntegrationLogger + IntegrationRetryable interface + tests | M | BR-65 |
| LAMS-0607 | Named + External Credentials (5) pointing at mocks | S | §16 |
| LAMS-0608 | CreditBureauService + HttpCalloutMock tests | L | BR-10 |
| LAMS-0609 | KycService (WSDL2Apex) + WebServiceMock tests | L | BR-10, BR-13 |
| LAMS-0610 | EligibilityService (Pass/Refer/Fail) + tests | L | BR-11, BR-12 |
| LAMS-0611 | Override Credit Score flow | S | BR-15 |

Depends on: 0606 before 0608/0609; 0610 before 0609 can call it.
**Exit:** AC-04, AC-05, AC-06.

### M07 – Documents and approval (≈ 18h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0701 | documentChecklist LWC (upload, verify, reject) + Jest | L | BR-16 – BR-18 |
| LAMS-0702 | ApplicationRouter + Document Verified flow + tests | M | BR-19, §13.3 |
| LAMS-0703 | Email templates EN/HI (submitted, doc rejected, approved, rejected) | M | BR-52 |
| LAMS-0704 | Loan Approval process (2 steps, Fail → Credit Head) | M | BR-21 – BR-24 |
| LAMS-0705 | Auto-approve path in the router | S | BR-27 |
| LAMS-0706 | Secured Loan Review orchestration | L | BR-20 |
| LAMS-0707 | LetterHeader, LetterFooter, LetterController, OfferLetter PDF | M | BR-28 |
| LAMS-0708 | Respond to Offer + Withdraw Application flows | M | BR-29, BR-32 |

**Exit:** AC-01, AC-02, AC-03.

### M08 – Servicing (≈ 24h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0801 | Offer Accepted flow + LoanAgreement PDF | M | BR-29, BR-33 |
| LAMS-0802 | LoanTrigger + LoanSharingService + tests | M | BR-70 |
| LAMS-0803 | EmiScheduleService + tests (AC-09) | M | BR-37, BR-39 |
| LAMS-0804 | PayoutService + Disburse Loan flow + tests | L | BR-34 – BR-37 |
| LAMS-0805 | emiSchedule + loanSummaryCard LWCs | M | BR-40, BR-49 |
| LAMS-0806 | PaymentTrigger + PaymentAllocationService (rebuild, advance, payoff, reversal) + tests | L | BR-42 – BR-46 |
| LAMS-0807 | LoanOverdueBatch + LoanOverdueScheduler + tests | L | BR-48 – BR-50 |
| LAMS-0808 | Waive Late Fee flow | S | BR-51 |
| LAMS-0809 | Prepayment Quote flow | S | BR-44 |
| LAMS-0810 | Send Notification subflow + remaining templates | M | BR-52, BR-54 |
| LAMS-0811 | SmsService (chunked @future) + tests | M | BR-53 |
| LAMS-0812 | Daily Reminders scheduled flow (incl. offer expiry) | M | BR-30, BR-31, BR-55 |
| LAMS-0813 | ClosureLetter PDF | S | BR-46 |

**Exit:** AC-07, AC-08, AC-10 (via test), AC-11, AC-12.

### M09 – Events and APIs (≈ 14h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-0901 | Loan Event Handler (platform event flow) | S | BR-50 |
| LAMS-0902 | CoreBankingSyncQueueable + LoanEventTrigger + PaymentChangeEventTrigger + tests | L | BR-38, BR-47 |
| LAMS-0903 | Integration User + External Client App (client credentials) | M | §16 |
| LAMS-0904 | LoanApplicationApi + tests | M | BR-06 |
| LAMS-0905 | PaymentCallbackApi + tests | M | BR-41 |
| LAMS-0906 | LoanStatusWebService + tests | S | BR-67 |
| LAMS-0907 | IntegrationRetryBatch + schedule + tests | M | BR-66 |
| LAMS-0908 | Postman collection in `postman/` | S | §16 |

**Exit:** Postman collection green; a failed call retries to Gave Up.

### M10 – Portal (≈ 12h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-1001 | Site on Aura Customer Service template, self-registration with PAN check | M | BR-59 |
| LAMS-1002 | lamsPortalTheme Aura theme layout | M | BR-60 |
| LAMS-1003 | Portal pages and components | L | BR-60 |
| LAMS-1004 | Sharing set + portal access tests | S | BR-59 |
| LAMS-1005 | Queues, Case assignment + escalation rules | S | BR-56, BR-58 |
| LAMS-1006 | Portal_Enabled__c off behaviour | S | BR-61 |

**Exit:** AC-13; a borrower applies, uploads, accepts and raises a request.

### M11 – Reports and dashboards (≈ 5h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-1101 | 4 custom report types | S | §18 |
| LAMS-1102 | Origination dashboard (dynamic) | M | BR-62 |
| LAMS-1103 | Portfolio dashboard (dynamic) | M | BR-63 |
| LAMS-1104 | Integrations dashboard | S | BR-64 |

### M12 – AI and Data Cloud (≈ 16h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-1201 | Agent actions (5 invocables) + tests | M | BR-76, BR-77 |
| LAMS-1202 | Application Summary prompt template | S | BR-77 |
| LAMS-1203 | Loan Officer Assistant | M | BR-77 |
| LAMS-1204 | Borrower Assistant in the portal + guardrail test (AC-15) | L | BR-75, BR-76 |
| LAMS-1205 | Data Cloud: ingest, map, identity resolution | L | BR-78 |
| LAMS-1206 | Calculated insights, segments, activation write-back | L | BR-78 |

### M13 – End to end and portfolio (≈ 8h)

| ID | Work item | Size | Delivers |
| --- | --- | --- | --- |
| LAMS-1301 | AC-16 run: Personal and Home loan, Draft to Closed | M | AC-16 |
| LAMS-1302 | Coverage ≥ 90% per class; fix gaps | M | NFR-10 |
| LAMS-1303 | README: architecture, setup steps, manual steps, screenshots | M | §19 |
| LAMS-1304 | 5-minute demo video; make repo public | S | – |

**Total ≈ 150 hours.** At 10 hours a week, about 15 weeks. Re-estimate after M02, which shows how fast you actually work.

## 5. Definitions

**Ready to start** when: it has BR/AC references and its dependencies are ticked.

**Done** (an item can close when):

- [ ] Metadata is in source control and deploys cleanly
- [ ] Apex: tests in the same commit/branch, ≥ 90% coverage for the class, bulk (200) and toggle on/off cases
- [ ] No hardcoded IDs, endpoints, thresholds or user-facing text (labels used)
- [ ] CI green
- [ ] BRD updated if the design changed
- [ ] Screenshot in `docs/images/` for anything visible (linked from the devlog)

## 6. PR self-review checklist

- [ ] Does it do only what the work item says?
- [ ] Bulk-safe: no SOQL/DML in loops
- [ ] Sharing and FLS respected (`with sharing`, `WITH USER_MODE` where right)
- [ ] Callouts before DML in the same transaction
- [ ] Feature toggle checked where the BRD lists one
- [ ] Error paths logged, not swallowed

## 7. Risks to watch

| Risk | Early check | Fallback |
| --- | --- | --- |
| Developer Edition limits (portal licences, orchestration runs, AI credits) | LAMS-0102 | Trim demo users; document what was simulated |
| Data Cloud / Agentforce features differ in the org | LAMS-0102 | Keep toggles off; build what the org allows, record the rest in the README |
| Mock endpoints throttle or change | LAMS-0106 | Keep `Mock_Response__c` in metadata as an in-org fallback |
| Scope creep | Parking-lot label | Only BR-referenced work enters a milestone |
