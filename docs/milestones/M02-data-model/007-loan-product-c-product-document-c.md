# LAMS-007 · Loan_Product__c + Product_Document__c

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** BRD §10.2

**Depends on:** M01 done (org connected to the CLI)

## Goal

Products are data, not code: each of the four loan products carries its own limits, rate, eligibility rules and document checklist. Every later rule (BR-03, BR-11, BR-16) reads from these two objects.

## Build

**Object `Loan_Product__c`** — label *Loan Product*, plural *Loan Products*; Name field = Text (Personal Loan, Home Loan, …); enable Reports, Track Field History, Search. Sharing (OWD) is set in LAMS-026; leave the default for now.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Product_Code__c | Text(2) | Required, Unique (case-insensitive), External ID. Values PL, HL, AL, BL |
| Min_Amount__c | Currency(16,2) | Required |
| Max_Amount__c | Currency(16,2) | Required |
| Min_Tenure__c | Number(3,0) | Required. Months |
| Max_Tenure__c | Number(3,0) | Required. Months |
| Interest_Rate__c | Percent(3,2) | Required. Annual rate, e.g. 14.00 |
| Min_Credit_Score__c | Number(3,0) | Required |
| Min_Monthly_Income__c | Currency(16,2) | Required |
| Max_EMI_To_Income__c | Percent(3,2) | Required |
| Max_LTV__c | Percent(3,2) | Optional. Blank = no LTV rule (Personal, Business) |
| Max_Age_At_Maturity__c | Number(3,0) | Required |
| Processing_Fee__c | Percent(3,2) | Required |
| Late_Fee__c | Percent(3,2) | Required. Per month on the overdue EMI |
| Grace_Days__c | Number(2,0) | Default 5 |
| Requires_Field_Verification__c | Checkbox | Default false. True for HL and BL |
| Auto_Approve_Eligible__c | Checkbox | Default false. True for PL only; the auto-approve rule reads this instead of a hardcoded product code (BR-27, BRD v2.1) |
| Record_Type_Name__c | Text(40) | DeveloperName of the application record type (Personal, Home, Auto, Business); used by the screen flow in LAMS-035 |
| Active__c | Checkbox | Default true |

**Object `Product_Document__c`** — label *Product Document*; Name = Auto Number `PD-{0000}`.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan_Product__c | Master-Detail(Loan_Product__c) | Related list label *Document Checklist*; child relationship name `Product_Documents` |
| Document_Type__c | Picklist (restricted) | PAN Card, Address Proof, Salary Slips, Bank Statement, ITR, GST Certificate, Property Papers, Vehicle Quotation |
| Mandatory__c | Checkbox | Default true |

**Global value set** `LAMS_Document_Type` with the 8 values above, used by Document_Type__c here and on Application_Document__c (LAMS-010), so the two lists can never drift.

**Also:** a tab for Loan_Product__c; add the Document Checklist related list to the product page layout.

## Steps

1. Create the global value set `LAMS_Document_Type`.
2. Create `Loan_Product__c` and its fields in Setup (Object Manager), or write the `.object-meta.xml` / `.field-meta.xml` files under `force-app/main/default/objects/`.
3. Create `Product_Document__c` with the Master-Detail field first, then the other fields.
4. Create the tab; update the page layout.
5. Retrieve everything into source:
   `sf project retrieve start --metadata CustomObject:Loan_Product__c CustomObject:Product_Document__c GlobalValueSet:LAMS_Document_Type CustomTab:Loan_Product__c`
6. Commit: `feat(data-model): Loan_Product__c and Product_Document__c [LAMS-007]`.

## Learn

- **Master-Detail vs Lookup:** the child has no owner of its own; its sharing, deletion and roll-ups follow the parent.
- **Global value sets** share one picklist definition across objects.
- **External ID + Unique** on Product_Code__c makes upserts by code possible (used by seed data in LAMS-016).
- Field precision: Currency(16,2) and Percent(3,2) — pick precision on purpose; changing it later can lose data.

## Done when

- [ ] Both objects and all fields exist in the org and in `force-app/` source
- [ ] `sf project deploy start --dry-run` from source succeeds
- [ ] In the UI you can create *Personal Loan* (PL) with two checklist rows, and deleting the product deletes its rows
- [ ] Creating a second product with code PL fails on the unique check
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.2 Loan_Product__c, §5 product seed values, BR-03, BR-11, BR-16
