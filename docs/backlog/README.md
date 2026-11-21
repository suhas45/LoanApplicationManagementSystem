# LAMS Backlog

The work tracker for the LAMS build: one checklist file per milestone, 93 work items, ≈ 151 hours. Do the milestones in order. Design and rules: [WORK_PLAN.md](../WORK_PLAN.md); requirements: [LAMS_BRD_v2.md](../LAMS_BRD_v2.md).

| Milestone | Items | Estimate | Exit criteria |
| --- | --- | --- | --- |
| [M01 – Org and repo](M01-org-and-repo.md) | 6 | ≈ 4h | a push to `main` passes CI. |
| [M02 – Data model](M02-data-model.md) | 10 | ≈ 12h | seed data loads; AC-09 EMI checks by hand on a record (₹8,979). |
| [M03 – Configuration](M03-configuration.md) | 5 | ≈ 6h | script runs; a toggle is readable from Apex and from a Flow. |
| [M04 – Security](M04-security.md) | 9 | ≈ 10h | AC-14 passes logged in as an Operations Officer. |
| [M05 – Validation rules](M05-validation-rules.md) | 3 | ≈ 4h | – |
| [M06 – Origination](M06-origination.md) | 11 | ≈ 18h | AC-04, AC-05, AC-06. |
| [M07 – Documents and approval](M07-documents-and-approval.md) | 8 | ≈ 18h | AC-01, AC-02, AC-03. |
| [M08 – Servicing](M08-servicing.md) | 13 | ≈ 24h | AC-07, AC-08, AC-10 (via test), AC-11, AC-12. |
| [M09 – Events and APIs](M09-events-and-apis.md) | 8 | ≈ 14h | Postman collection green; a failed call retries to Gave Up. |
| [M10 – Portal](M10-portal.md) | 6 | ≈ 12h | AC-13; a borrower applies, uploads, accepts and raises a request. |
| [M11 – Reports and dashboards](M11-reports-and-dashboards.md) | 4 | ≈ 5h | – |
| [M12 – AI and Data Cloud](M12-ai-and-data-cloud.md) | 6 | ≈ 16h | – |
| [M13 – End to end and portfolio](M13-end-to-end-and-portfolio.md) | 4 | ≈ 8h | – |

## How to update

| State | Write it as |
| --- | --- |
| Not started | `- [ ] **LAMS-0606** · …` |
| In progress | `- [ ] **LAMS-0606** · … **(in progress)**` |
| Done | `- [x] **LAMS-0606** · … — done 2026-11-30` |
| Dropped | `- [x] ~~**LAMS-0606** · …~~ — dropped: reason` |

- Keep **one** item in progress at a time.
- Tick the box only when the item meets the Definition of Done in [WORK_PLAN.md §5](../WORK_PLAN.md).
- Commit the tick on its own or with the work: `chore(backlog): done LAMS-0606`.
- New work found mid-way goes under **Parking lot** in that milestone's file, with the next free ID if you decide to do it.

## Check progress

```
python scripts/backlog/progress.py
```
