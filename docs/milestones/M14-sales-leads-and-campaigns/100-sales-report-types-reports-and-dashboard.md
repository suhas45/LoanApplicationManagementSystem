# LAMS-100 · Sales report types, reports and Sales dashboard

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** M (2–5h) · **Delivers:** BR-89

**Depends on:** LAMS-095 (Lead fields, First_Contacted_At__c, Lead FLS on LAMS_Sales_Access), LAMS-096 (Product_Code__c, First_Contact_Overdue__c, queues), LAMS-098 (converted leads and their applications, Source_Lead_Id__c), LAMS-099 (Campaign__c, campaign members, AC-18 demo data), LAMS-012 (Loan__c Principal__c, Disbursement_Status__c), LAMS-024 (`LAMS_Reports`). M11 comes after M14, so this item creates its own folders and doesn't need LAMS-080.

## Goal

The Credit Head sees the sales funnel on one dashboard (BR-89):

- leads by source and status
- lead-to-application conversion rate (success metric ≥ 30%, §9)
- time to first contact
- leads still waiting for a first call (BR-84)
- applications and disbursed amount by campaign

Campaign results come from `Loan_Application__c.Campaign__c`, because Salesforce's campaign influence is built on Opportunities and LAMS creates none (§10.12, C5). This item also finishes **AC-18**: the campaign report counts the pre-approved borrower's application.

## Build

**Helper formula fields on Lead** (proposed; Read FLS on LAMS_Sales_Access; the admin, as Credit Head, reads them as System Administrator)

| Field (API name) | Type | Formula | Used by |
| --- | --- | --- | --- |
| `Converted_Count__c` | Formula (Number, 0 dp) | `IF(IsConverted, 1, 0)` | Conversion rate: a summary formula can sum a number, not a checkbox |
| `Hours_To_First_Contact__c` | Formula (Number, 1 dp) | `IF(ISBLANK(First_Contacted_At__c), NULL, (First_Contacted_At__c - CreatedDate) * 24)` | Average time to first contact, in calendar hours. Business hours would need Apex `BusinessHours.diff`; record that as a known simplification |

Each conversion creates exactly one application (LAMS-098 rolls the conversion back otherwise), so *converted leads ÷ leads* **is** the lead-to-application rate.

**Custom report types** (Category *Other Reports*, Deployed; §18)

| Report type (API name) | Primary → related | Relationship | Extra fields via lookup |
| --- | --- | --- | --- |
| Leads with Campaign (`Leads_with_Campaign`) | Lead → Campaign Members (Campaign History) | A with or without B | Campaign Member → Campaign: Name, Type, Status, Active; Lead: Owner Full Name, Loan Product Name |
| Applications with Campaign (`Applications_with_Campaign`) | Loan_Application__c → Loan__c (`Loans`) | A with or without B (most applications never reach a loan) | Campaign__c: Name, Type, Active; Loan_Product__c: Name, Product_Code__c; Borrower__c: Name; Owner: Full Name |

Field layouts: *Lead* (Name, Company, Lead Source, Status, Product Code, Requested Amount, City, Created Date, First Contacted At, Hours To First Contact, Converted, Converted Count, First Contact Overdue) · *Campaign Member* (Status, Responded, Created Date). And *Application* (Name, Status, Channel, Amount, Approved Amount, Submitted Date, Campaign, Source Lead Id) · *Loan* (Name, Status, Disbursement Status, Disbursement Date, Principal). Leave PAN and income out of both layouts (AC-14 still holds through FLS).

**Row multiplication.** A lead in two campaigns appears twice in *Leads with Campaign*, so the funnel reports use the standard **Leads** report type. An application has at most one loan (`Application_Key__c` is unique, LAMS-012), so *Applications with Campaign* never double-counts.

**Folders** (proposed names)

| Folder | Shared with |
| --- | --- |
| LAMS Sales Reports | Roles: Credit Head (View); Roles and subordinates: Credit Manager (View) |
| LAMS Sales Dashboards | Role: Credit Head only. Anyone who opens a static dashboard sees the running user's data |

**Reports** in *LAMS Sales Reports* (names proposed). Default date filter: Created Date = LAST 90 DAYS (proposed).

| Report | Report type | Format and groupings | Filters | Summaries |
| --- | --- | --- | --- | --- |
| Leads by Source and Status | Leads (standard) | Matrix: rows Lead Source, columns Status | – | Record Count |
| Lead Conversion Rate | Leads | Summary by Lead Source | – | Record Count; Sum Converted_Count__c; summary formula **Conversion Rate** = `Lead.Converted_Count__c:SUM / RowCount`, Percent, 1 dp, shown at every grouping level and the grand total |
| Time to First Contact | Leads | Summary by Lead Source, then Owner | First_Contacted_At__c not blank | Average Hours_To_First_Contact__c; Record Count |
| Leads Awaiting First Contact | Leads | Tabular: Name, Owner, Product Code, City, Lead Source, Created Date | First_Contact_Overdue__c = true (no date filter) | Record Count |
| Leads by Campaign | Leads with Campaign | Summary by Campaign Name, then Member Status | Campaign Name not blank | Record Count |
| Applications by Campaign | Applications with Campaign | Summary by Campaign Name, then Application Status | Campaign not blank; Created Date = LAST 365 DAYS | Record Count; Sum Amount__c |
| Disbursed Amount by Campaign | Applications with Campaign | Summary by Campaign Name | Campaign not blank; Loan Disbursement Status = Disbursed | Sum Loan Principal__c; Record Count |

**Dashboard *LAMS Sales*** (folder *LAMS Sales Dashboards*)

| Setting | Value |
| --- | --- |
| View dashboard as | **Another person: the Credit Head**. In `Lams` that is the admin user, who holds LAMS_Credit_Head_Group and Marketing User. Static (`dashboardType = SpecifiedUser`); record the username in the README |
| Scheduled refresh | Daily 08:00 (proposed). No email subscription: the org allows about 15 emails a day |

| Component | Source report | Chart |
| --- | --- | --- |
| Leads (90 days) | Leads by Source and Status | Metric |
| Leads by source and status | Leads by Source and Status | Stacked horizontal bar: Lead Source × Status |
| Lead-to-application rate | Lead Conversion Rate | Gauge on Conversion Rate, 0–100%: red < 15%, amber 15–30%, green ≥ 30% (success metric, §9) |
| Avg hours to first contact | Time to First Contact | Vertical bar by Lead Source |
| Awaiting first contact | Leads Awaiting First Contact | Metric (red when > 0) and a Lightning table |
| Applications by campaign | Applications by Campaign | Stacked bar: Campaign × Status |
| Disbursed by campaign (₹) | Disbursed Amount by Campaign | Horizontal bar, Sum Principal |

**Demo data.** Keep it small (5 MB storage). The leads from LAMS-096 – LAMS-099 plus about 6 more is enough. Use a script `scripts/apex/seed-sales-demo.apex` (proposed) with a plain insert (no assignment rule, so no emails):

| Leads | Source | Status | Notes |
| --- | --- | --- | --- |
| 2 | Website | 1 Contacted, 1 New | |
| 2 | Branch Walk-in | 1 Qualified → convert with *Convert to Application*, 1 Unqualified (Not Eligible) | |
| 2 | Campaign | 1 Responded member of the top-up campaign, converted; 1 New | |

The flow stamps First_Contacted_At__c at the moment of the status change, so live demo leads show near-zero hours. For realistic values, either give your user *Set Audit Fields upon Record Creation* (Setup → User Interface, then a permission set) and insert those leads with a past `CreatedDate`, or just explain the metric. Delete the demo leads afterwards if storage gets tight.

## Steps

1. Create the two Lead formula fields and their FLS.
2. Create both report types and their field layouts.
3. Create the folders and share them as listed.
4. Run the demo script; convert the two leads marked above.
5. Build the seven reports, then the dashboard; set the running user and the refresh.
6. **AC-18 (report part):** open *Applications by Campaign* and confirm the top-up campaign counts Aarav Sharma's submitted application from LAMS-099. *Leads by Campaign* shows the campaign lead.
7. Check the numbers by hand on a small set: count of converted ÷ count of leads per source matches the gauge, and one lead's hours = (First Contacted At − Created Date) × 24.
8. Retrieve (check the real folder API names first with `sf org list metadata --metadata-type ReportFolder --target-org Lams`):
   `sf project retrieve start --metadata ReportType:Leads_with_Campaign ReportType:Applications_with_Campaign CustomField:Lead.Converted_Count__c CustomField:Lead.Hours_To_First_Contact__c "Report:LAMS_Sales_Reports/*" "Dashboard:LAMS_Sales_Dashboards/*" ReportFolder DashboardFolder PermissionSet:LAMS_Sales_Access --target-org Lams`
9. Screenshot the dashboard into `docs/BRD/images/` and link it from the devlog.
10. Commit: `feat(reports): sales report types, reports and Sales dashboard [LAMS-100]`.

## Learn

- **Campaign influence needs Opportunities.** The standard Campaign ROI and influence reports read Opportunity amounts. With applications instead of opportunities, a custom report type on the object that carries the campaign lookup is the replacement.
- **Summary formulas** work on summarised numbers: `RowCount` and `FIELD:SUM`. A checkbox can't be summed, so a 0/1 formula field turns *Converted* into a countable value.
- **Row multiplication** in parent-with-children report types: pick the report type whose primary object is the thing you count, or a 1:1 child relationship.
- **Static dashboards** show the running user's data to every viewer, so restrict the folder. They don't use the limited dynamic-dashboard allowance and can be scheduled.

## Done when

- [ ] Both report types are Deployed and listed under Other Reports; the two Lead formula fields exist
- [ ] The seven reports return the demo data: leads by source and status, a conversion rate per source and in total, average hours to first contact, awaiting-first-contact leads, leads by campaign, applications and disbursed amount by campaign
- [ ] **AC-18 (report part):** *Applications by Campaign* counts the pre-approved borrower's application under the top-up campaign
- [ ] The *LAMS Sales* dashboard runs as the Credit Head (the admin in `Lams`), shows all seven components, and only the Credit Head role can open its folder
- [ ] An Operations Officer can't open the sales folders (if that user exists in your org; otherwise note it)
- [ ] Report types, reports, dashboard and fields are in source; the running-user username is noted in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-84, BR-89; §9 AC-18 and success metric "Leads converted to applications ≥ 30%"; §10.12 Campaign__c and the campaign-influence note; §11 FLS, LAMS_Reports; §18 Custom report types (Leads with Campaign, Applications with Campaign) and Sales dashboard; §8 C1; Appendix C (C5)
