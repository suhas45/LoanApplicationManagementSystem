# LAMS-080 · 4 custom report types

**Milestone:** [M11 – Reports and dashboards](README.md) · **Size:** S (≤ 2h) · **Delivers:** §18

**Depends on:** LAMS-009 / LAMS-010 (Loan_Application__c, Application_Document__c), LAMS-012 / LAMS-013 (Loan__c, EMI_Instalment__c, Payment__c), LAMS-014 (Integration_Log__c), LAMS-027 (FLS, so AC-14 holds in reports), LAMS-024 (`LAMS_Reports`)

## Goal

Create the four custom report types that the three dashboards are built on, with the fields people need already in the field picker (BR-62 – BR-64, §18).

## Build

All four: Category **Other Reports**, Deployment Status **Deployed**. "With or without" keeps parents that have no children yet.

| Report type (API name) | Primary → related | Relationship | Extra fields via lookup |
| --- | --- | --- | --- |
| Applications with Documents (`Applications_with_Documents`) | Loan_Application__c → Application_Document__c | A records with or without B | Loan_Product__c: Name, Product_Code__c; Owner: Full Name; Borrower__c: Name |
| Loans with Instalments (`Loans_with_Instalments`) | Loan__c → EMI_Instalment__c | A with or without B (Pending Disbursement loans have no rows yet) | Loan_Product__c: Name; Assigned_Officer__c: Full Name; Borrower__c: Name |
| Loans with Payments (`Loans_with_Payments`) | Loan__c → Payment__c | A with or without B | Loan_Product__c: Name; Assigned_Officer__c: Full Name |
| Integration Logs (`Integration_Logs`) | Integration_Log__c | Single object | Created By: Full Name |

**Field layout sections** (rename the default ones; remove system fields nobody reports on):

| Report type | Sections |
| --- | --- |
| Applications with Documents | *Application* (Name, Status, Channel, Amount, Approved Amount, Tenure, Eligibility Result, Credit Score Source, Rejection Reason, Submitted Date, Decision Date, Offer Expiry Date) · *Product* · *Document* (Document Type, Mandatory, Status, Rejection Reason, Verified Date) |
| Loans with Instalments | *Loan* (Name, Status, Principal, Net Disbursement, Outstanding Principal, Overdue Amount, Days Past Due, Overdue Bucket, Disbursement Date) · *Instalment* (No, Due Date, EMI Amount, Late Fee, Amount Paid, Balance Due, Status) |
| Loans with Payments | *Loan* (as above) · *Payment* (Reference, Payment Date, Amount, Mode, Status) |
| Integration Logs | Integration, Direction, Status, HTTP Status, Duration Ms, Retry Count, Next Retry At, Related Record Id, Correlation Id, Created Date |

PAN, income and score stay out of the default layout; FLS still hides them from Operations if anyone adds them (AC-14). `Request__c` / `Response__c` are left out of the Integration Logs layout (proposed).

**Report folders** (create now; reports come in LAMS-081 – LAMS-083; names proposed)

| Folder | Viewers |
| --- | --- |
| LAMS Origination Reports | Roles and subordinates: Credit Manager; role Credit Head |
| LAMS Portfolio Reports | Roles: Operations Officer, Credit Head |
| LAMS Integration Reports | Role: Credit Head |

## Steps

1. Setup → Report Types → New, once per row above; edit the field layout.
2. Create the three report folders and share them as listed.
3. Check in Reports → New Report that each type appears under *Other Reports* with the sections.
4. As an Operations Officer, open *Loans with Instalments* → Borrower lookup fields: PAN is not offered (AC-14).
5. Retrieve: `sf project retrieve start --metadata ReportType:Applications_with_Documents ReportType:Loans_with_Instalments ReportType:Loans_with_Payments ReportType:Integration_Logs ReportFolder`
6. Commit: `feat(reports): four custom report types and folders [LAMS-080]`.

## Learn

- **Custom report types** fix the join (inner "with" or outer "with or without") and the field list; standard per-object types exist too ("Loan Applications", "Loans") once *Allow Reports* is on.
- **Row multiplication:** a parent-with-children report has one row per child. Count applications or sum loan principal from the single-object type, or you count each parent once per document or instalment.
- Reports respect FLS and sharing of the running user, which is what makes dynamic dashboards and AC-14 work.
- Folder sharing controls who can open reports; it does not change which rows they see.

## Done when

- [ ] All four report types are Deployed and visible under Other Reports
- [ ] A test report on each type returns rows from demo data
- [ ] An Operations Officer cannot add PAN, income or score to any report (AC-14)
- [ ] Report types and folders are in source
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §18 Custom report types, §11 FLS and `LAMS_Reports`, §10.3 – §10.9, BR-62, BR-63, BR-64, BR-71, AC-14
