# LAMS-081 · Origination dashboard (dynamic)

**Milestone:** [M11 – Reports and dashboards](README.md) · **Size:** M (2–5h) · **Delivers:** BR-62

**Depends on:** LAMS-080 (report types, folders), LAMS-016 (demo data), LAMS-029 (Loan Officers, Credit Manager, Credit Head users), LAMS-022 (role hierarchy), LAMS-044 (manual overrides exist)

## Goal

Credit Managers see applications by status and product, approval rate, rejection reasons, average days to decision and manual overrides for **their own team only**, from one dynamic dashboard (BR-62, O1, O2).

## Build

**Reports** in *LAMS Origination Reports* (names proposed). "Loan Applications" is the standard single-object report type, used so each application counts once.

| Report | Type | Format, groupings | Filters | Summaries |
| --- | --- | --- | --- | --- |
| Applications by Status and Product | Loan Applications | Matrix: rows Status__c, columns Loan Product | Status ≠ Draft; Created Date = all time (demo) | Record Count |
| Approval Rate | Loan Applications | Summary by bucket field *Decision Outcome* on Status__c: **Approved** = Approved, Offer Accepted, Offer Declined, Expired, Withdrawn (with a decision date these were all approved first); **Rejected** = Rejected | Decision_Date__c ≠ blank | Record Count |
| Rejection Reasons | Loan Applications | Summary by Rejection_Reason__c | Status = Rejected | Record Count |
| Average Days to Decision | Loan Applications | Summary by Loan Product | Decision_Date__c ≠ blank | Row-level formula *Days to Decision* = `Loan_Application__c.Decision_Date__c - DATEVALUE(Loan_Application__c.Submitted_Date__c)` (Number, 1 dp), Average |
| Manual Overrides | Loan Applications | Tabular: Name, Loan Product, Credit Score Source, Override Reason, Eligibility Result, Owner | Credit_Score_Source__c = Manual Override | Record Count |
| Documents Pending Verification (optional) | Applications with Documents | Summary by Application Name | Document Status = Uploaded | Record Count |

**Dashboard** *LAMS Origination* (folder *LAMS Dashboards*, proposed, shared with roles Credit Manager and subordinates and Credit Head)

| Setting | Value |
| --- | --- |
| View dashboard as | **Me** (dashboard viewer) — dynamic, `dashboardType = LoggedInUser` |
| Let authorized users change running user | On (Credit Head can view as a Credit Manager; needs *View My Team's Dashboards*) |
| Dashboard filter | Loan Product (proposed) |

| Component | Source report | Chart |
| --- | --- | --- |
| Open pipeline | Applications by Status and Product | Metric: record count |
| Applications by status and product | Applications by Status and Product | Stacked horizontal bar (Y = Status, stack = Product) |
| Approval rate | Approval Rate | Donut, show percentages |
| Rejection reasons | Rejection Reasons | Horizontal bar, sorted descending |
| Avg days to decision | Average Days to Decision | Vertical bar by product (target lines: 2 for PL, 5 secured — success metrics) |
| Manual overrides | Manual Overrides | Lightning table (top 10) |

## Steps

1. Check demo data covers several statuses and owners; if not, add 10–20 applications across both Loan Officers (data tree or anonymous Apex in `scripts/data/`).
2. Build each report in Lightning Report Builder; save to *LAMS Origination Reports*.
3. Create the dashboard folder and dashboard; set *View dashboard as: Me*; add components and the filter.
4. Log in as Loan Officer 1, Loan Officer 2, the Credit Manager and the Credit Head (Setup → Users → Login) and refresh the dashboard for each.
5. Retrieve: `sf project retrieve start --metadata "Report:LAMS_Origination_Reports/*" "Dashboard:LAMS_Dashboards/*" DashboardFolder ReportFolder` (use the actual folder API names).
6. Commit: `feat(reports): Origination dynamic dashboard [LAMS-081]`.

## Learn

- **Dynamic dashboards** run each viewer's own sharing ("View as: Me"); role hierarchy then gives a Credit Manager their team's applications. Developer Edition allows only a few (§18); check the count before building LAMS-082.
- Dynamic dashboards cannot be saved in private folders and cannot be scheduled to refresh; viewers refresh them.
- **Bucket fields** group picklist values without new fields; **row-level formulas** add one calculated column per report (here, days to decision).
- Reports have no median; the success metric "median days" is checked by exporting the report (BRD §9), the dashboard shows the average.

## Done when

- [ ] All five reports and the dashboard exist and render with demo data
- [ ] Loan Officer 1 and Loan Officer 2 see different totals; the Credit Manager sees both officers' applications; the Credit Head sees all (BR-62)
- [ ] An Operations Officer cannot open the dashboard's reports (folder access)
- [ ] Reports, dashboard and folders are in source; the running-user setting is noted in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §18 Dashboards (Origination) and DE limit note, §9 success metrics, §11 role hierarchy, §10.3 fields, BR-15, BR-62, O1, O2, C1
