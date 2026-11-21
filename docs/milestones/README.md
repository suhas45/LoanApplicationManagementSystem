# LAMS – Milestones and Work Items

The build of the [BRD](../BRD/LAMS_BRD.md) is divided into 13 milestones and 93 work items (LAMS-001 – LAMS-093), about 150 hours. Do the milestones in order. This page is the index and the rulebook; each milestone folder holds its checklist and one file per work item.

## Milestones

| Milestone | Work items | Estimate | Exit criteria |
| --- | --- | --- | --- |
| [M01 – Org and repo](M01-org-and-repo/README.md) | 001 – 006 | ≈ 4h | A push to `main` passes CI |
| [M02 – Data model](M02-data-model/README.md) | 007 – 016 | ≈ 12h | Seed data loads; AC-09 EMI checks by hand |
| [M03 – Configuration](M03-configuration/README.md) | 017 – 021 | ≈ 6h | Toggles readable from Apex and Flow |
| [M04 – Security](M04-security/README.md) | 022 – 030 | ≈ 10h | AC-14 |
| [M05 – Validation rules](M05-validation-rules/README.md) | 031 – 033 | ≈ 4h | Every rule has a negative test |
| [M06 – Origination](M06-origination/README.md) | 034 – 044 | ≈ 18h | AC-04, AC-05, AC-06 |
| [M07 – Documents and approval](M07-documents-and-approval/README.md) | 045 – 052 | ≈ 18h | AC-01, AC-02, AC-03 |
| [M08 – Servicing](M08-servicing/README.md) | 053 – 065 | ≈ 24h | AC-07, AC-08, AC-10, AC-11, AC-12 |
| [M09 – Events and APIs](M09-events-and-apis/README.md) | 066 – 073 | ≈ 14h | Postman collection green; retry reaches Gave Up |
| [M10 – Portal](M10-portal/README.md) | 074 – 079 | ≈ 12h | AC-13; borrower self-service works |
| [M11 – Reports and dashboards](M11-reports-and-dashboards/README.md) | 080 – 083 | ≈ 5h | Dynamic dashboards differ per user |
| [M12 – AI and Data Cloud](M12-ai-and-data-cloud/README.md) | 084 – 089 | ≈ 16h | AC-15; clean payer gets Pre_Approved__c |
| [M13 – End to end and portfolio](M13-end-to-end-and-portfolio/README.md) | 090 – 093 | ≈ 8h | AC-16; coverage ≥ 90% |

Check progress any time:

```
python scripts/backlog/progress.py
```

## Folder layout

```
docs/
├── BRD/                       requirements and solution design
└── milestones/
    ├── README.md              this page
    ├── DEVLOG.md              one entry per finished milestone
    └── M06-origination/
        ├── README.md          goal, exit criteria, checklist (tick here), parking lot
        ├── 034-emicalculator-lwc-jest-tests.md
        └── …                  one file per work item: what to build, steps, checks
```

Each work item file has the same sections: **Depends on**, **Goal**, **Build** (exact spec), **Steps**, **Learn** (Salesforce concepts practised), **Done when** (checks), **References** (BRD sections).

## How to track

Status lives only in the milestone's README checklist, never in the work item file.

| State | Write it as |
| --- | --- |
| Not started | `- [ ] [LAMS-041](…) · …` |
| In progress | `- [ ] [LAMS-041](…) · … **(in progress)**` |
| Done | `- [x] [LAMS-041](…) · … — done 2026-11-30` |
| Dropped | `- [x] ~~[LAMS-041](…) · …~~ — dropped: reason` |

Rules:

- **One item in progress at a time.** Finish before starting the next.
- Follow milestone order; inside a milestone, follow its "Order" note and each item's **Depends on**.
- **Tests ship with the class** in the same work item, never later.
- Bugs or ideas found mid-work go under **Parking lot** in that milestone's README. If you decide to do one, give it the next free number after 093 and add a work item file.
- Sizes: `S` ≤ 2h · `M` 2–5h · `L` 5–10h. Anything bigger is split.

## Workflow per work item

1. Mark it **(in progress)**. Create a branch: `feat/LAMS-041-credit-bureau` (or `fix/…`, `chore/…`).
2. Follow the work item file. Build in the org and retrieve (`sf project retrieve start`), or write source and deploy.
3. Commit with the ID: `feat(apex): CreditBureauService with retry [LAMS-041]`.
4. Run the self-review checklist below. Push; CI validates the deploy and runs local tests. Fix until green.
5. Merge to `main`.
6. Tick the box with the date and commit: `chore(backlog): done LAMS-041`.

**Closing a milestone:** demo the exit criteria, tick the exit checklist, write a [DEVLOG](DEVLOG.md) entry, and update the BRD if the design changed.

**Weekly rhythm:** Sunday, run `progress.py` and pick the next 3–4 items. One item per session. Friday, update the devlog.

## Definition of Done

A work item is done when:

- [ ] Everything in its **Done when** section is true
- [ ] Metadata is in source control and deploys cleanly
- [ ] Apex: tests in the same branch, ≥ 90% coverage for the class, bulk (200 records) and toggle on/off cases
- [ ] No hardcoded IDs, endpoints, thresholds or user-facing text (custom labels used)
- [ ] CI green
- [ ] BRD updated if the design changed
- [ ] A screenshot in `docs/BRD/images/` for anything visible, linked from the devlog

## Self-review checklist (before merging)

- [ ] Does it do only what the work item says?
- [ ] Bulk-safe: no SOQL or DML inside loops
- [ ] Sharing and FLS respected (`with sharing`, `WITH USER_MODE` where right)
- [ ] Callouts before DML in the same transaction
- [ ] Feature toggle checked where the BRD lists one
- [ ] Error paths logged, not swallowed

## Risks to watch

| Risk | Early check | Fallback |
| --- | --- | --- |
| Developer Edition limits (portal licences, orchestration runs, AI credits) | LAMS-002 | Trim demo users; document what was simulated |
| Data Cloud or Agentforce features differ in the org | LAMS-002 | Keep toggles off; build what the org allows, note the rest in the README |
| Mock endpoints throttle or change | LAMS-006 | Keep `Mock_Response__c` in metadata as an in-org fallback |
| Scope creep | Parking lot | Only BR-referenced work enters a milestone |
