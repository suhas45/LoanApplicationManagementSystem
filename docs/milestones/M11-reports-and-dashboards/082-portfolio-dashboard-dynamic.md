# LAMS-082 · Portfolio dashboard (dynamic)

**Milestone:** [M11 – Reports and dashboards](README.md) · **Size:** M (2–5h) · **Delivers:** BR-63

**Depends on:** LAMS-080 (report types, folders), LAMS-054 (Loan__c shared to Assigned_Officer__c), LAMS-058 (payments allocated), LAMS-059 (Days_Past_Due__c, buckets), LAMS-029 (two Operations Officers), LAMS-081 (dashboard folder; confirms the dynamic dashboard limit)

## Goal

Each Operations Officer sees amount disbursed, outstanding principal, overdue by bucket and collected vs due this month for **their own loans**, and the Credit Head sees the whole book (BR-63, O4).

## Build

**Reports** in *LAMS Portfolio Reports* (names proposed)

| Report | Type | Format, groupings | Filters | Summaries |
| --- | --- | --- | --- | --- |
| Amount Disbursed | Loans | Summary by Disbursement_Date__c (calendar month), then Loan Product | Disbursement_Status__c = Disbursed | Sum Principal__c, Sum Net_Disbursement__c |
| Outstanding Principal | Loans | Summary by Loan Product | Status__c = Active | Sum Outstanding_Principal__c, Record Count |
| Overdue by Bucket | Loans | Summary by bucket field *DPD Bucket* on Days_Past_Due__c: 1–30 Soft, 31–60 Watch, 61–90 Substandard, 91+ Critical | Status = Active, Days_Past_Due__c > 0 | Sum Overdue_Amount__c, Record Count |
| Due This Month | Loans with Instalments | Summary by Loan Product | Instalment Due_Date__c = THIS MONTH; Instalment Status ≠ Cancelled | Sum EMI_Amount__c, Sum Late_Fee__c |
| Collected This Month | Loans with Payments | Summary by Loan Product | Payment_Date__c = THIS MONTH; Payment Status = Success | Sum Amount__c |
| My Overdue Loans | Loans | Tabular: Name, Borrower, Days Past Due, Overdue Bucket, Overdue Amount, Next Due Date | Days_Past_Due__c > 0 | Record Count |

The bucket field (not `Overdue_Bucket__c`) is used for grouping so the chart shows Soft → Critical in order; text formulas sort alphabetically. The ranges match BR-49.

**Dashboard** *LAMS Portfolio* (folder *LAMS Dashboards*)

| Setting | Value |
| --- | --- |
| View dashboard as | **Me** (dynamic, `LoggedInUser`) |
| Let authorized users change running user | On (Credit Head) |

| Component | Source report | Chart |
| --- | --- | --- |
| Disbursed (all time) | Amount Disbursed | Metric: Sum Net Disbursement |
| Disbursed by month | Amount Disbursed | Vertical bar by month |
| Outstanding principal | Outstanding Principal | Metric + donut by product |
| Overdue by bucket | Overdue by Bucket | Vertical bar, Sum Overdue Amount |
| Due this month | Due This Month | Metric |
| Collected this month | Collected This Month | Metric (placed next to *Due this month*) |
| My overdue loans | My Overdue Loans | Lightning table, sorted by Days Past Due desc |

## Steps

1. Check demo data: at least one Active loan per Operations Officer, some overdue (run LoanOverdueBatch on backdated instalments) and a payment this month.
2. Build the reports; save to *LAMS Portfolio Reports*.
3. Build the dashboard as above; save; confirm it saved as dynamic (DE limit, C1).
4. Log in as Operations Officer 1 (Salesforce) and Operations Officer 2 (Salesforce Platform; reports and loans work on that licence); refresh and compare. In the `Lams` org the Credit Head is the admin (LAMS-029), who sees every loan through View All Data, so check the whole-book total as the admin.
5. As an Operations Officer, confirm no PAN, income or score appears on any component or drill-down (AC-14).
6. Retrieve: `sf project retrieve start --metadata "Report:LAMS_Portfolio_Reports/*" "Dashboard:LAMS_Dashboards/*"` (actual folder API names).
7. Commit: `feat(reports): Portfolio dynamic dashboard [LAMS-082]`.

## Learn

- **Apex managed sharing feeds reports:** Operations Officers see loans through `Loan__Share` rows with reason Assigned_Officer (LAMS-054); the dynamic dashboard shows exactly that.
- **Two reports cannot be combined in one chart** component; "collected vs due" is two metrics side by side (a joined report is the alternative, with more limits).
- Relative date filters (THIS MONTH) keep the dashboard current without edits.
- Roll-up and formula fields (Overdue_Amount__c, Outstanding_Principal__c) can be summed in reports like normal currency fields.

## Done when

- [ ] All six reports and the dashboard render with demo data
- [ ] Operations Officer 1 and Operations Officer 2 see different totals; the Credit Head sees the sum (BR-63)
- [ ] Overdue by bucket shows Soft, Watch, Substandard, Critical in that order
- [ ] No PAN, income or score is visible to an Operations Officer anywhere on the dashboard (AC-14)
- [ ] Reports and dashboard in source
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §18 Dashboards (Portfolio) and DE limit note, §10.5 – §10.7, §11 Apex managed sharing and FLS, BR-49, BR-63, BR-70, BR-71, AC-14, C1
