# LAMS-012 · Loan__c with Application_Key__c, encrypted Payout_Account__c

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** §10.5

**Depends on:** LAMS-009 (Loan_Application__c); LAMS-007, LAMS-008 for the product and borrower lookups

## Goal

An accepted offer becomes a Loan__c record that carries the terms, disbursement and servicing state (BR-29, BR-33 – BR-37). A unique text key guarantees one loan per application (appendix #6), and the payout account number is stored encrypted and shown masked (BR-72). The roll-ups that need child objects follow in LAMS-013.

## Build

**Object `Loan__c`** — label *Loan*, plural *Loans*; Name = Auto Number `LN-{000000}` starting at 1; enable Reports, Activities (payout-failure and overdue tasks), Track Field History (fields in LAMS-028), Search, Bulk API, Streaming API (needed for CDC in LAMS-014). OWD (Private) is LAMS-026; the Apex sharing reason `Assigned_Officer` is added in LAMS-054.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan_Application__c | Lookup(Loan_Application__c) | Required; *Don't allow deletion*; child relationship `Loans` |
| Application_Key__c | Text(18) | Required, Unique (case-sensitive, proposed). Set to the application Id by the Offer Accepted flow (LAMS-053) |
| Borrower__c | Lookup(Contact) | Required (proposed; the portal sharing set needs it); *Don't allow deletion*; child relationship `Loans` |
| Loan_Product__c | Lookup(Loan_Product__c) | Required (proposed); *Don't allow deletion*; child relationship `Loans` |
| Principal__c | Currency(16,2) | Required. = Approved_Amount__c |
| Interest_Rate__c | Percent(3,2) | Copied from the application |
| Tenure__c | Number(3,0) | Months; copied |
| EMI_Amount__c | Currency(16,2) | Copied |
| Processing_Fee_Amount__c | Currency(16,2) | Principal × product fee |
| Net_Disbursement__c | Formula (Currency, 2 dp) | `Principal__c - BLANKVALUE(Processing_Fee_Amount__c, 0)` (BR-35) |
| Status__c | Picklist (restricted) | Pending Disbursement (default), Active, Closed |
| Closure_Type__c | Picklist (restricted) | Matured, Prepaid |
| Assigned_Officer__c | Lookup(User) | Lookup filter `User.IsActive = true` (proposed); child relationship `Assigned_Loans`. Drives Apex managed sharing |
| Disbursement_Status__c | Picklist (restricted) | Pending (default), In Progress, Disbursed, Failed |
| Disbursement_Date__c | Date | |
| Disbursement_Reference__c | Text(30) | UTR (proposed length) |
| Payout_Account__c | Text (Encrypted), length 20 (proposed) | Mask type *Last Four Characters Clear*, mask character `X`. Borrower's account, or the dealer's for Auto |
| Core_Banking_Sync_Status__c | Picklist (restricted) | Pending, Synced, Failed. No default (proposed; blank means sync is off or not yet attempted) |
| Days_Past_Due__c | Number(4,0) | Default 0. Set nightly (LAMS-059) |
| Overdue_Bucket__c | Formula (Text) | See below (BR-49) |

```
IF(BLANKVALUE(Days_Past_Due__c, 0) <= 0, "Current",
  IF(Days_Past_Due__c <= 30, "Soft",
  IF(Days_Past_Due__c <= 60, "Watch",
  IF(Days_Past_Due__c <= 90, "Substandard", "Critical"))))
```

Day 90 counts as Substandard and 91 onwards as Critical (BR-49 says "61–90" and "90+"; the boundary is resolved this way, proposed).

**Built in LAMS-013:** Total_Paid__c, Principal_Repaid__c, Outstanding_Principal__c, Overdue_Amount__c, Next_Due_Date__c (they need EMI_Instalment__c and Payment__c).

**Also:** a tab for Loan__c (LAMS-015 adds it to the app); *Loans* related list on the application and Contact layouts.

## Steps

1. Create the object, then the lookups, then the other fields.
2. For Payout_Account__c choose the field type *Text (Encrypted)* (classic encryption; no Shield licence needed).
3. Create the tab and add the related lists.
4. Test by hand: create a loan for an existing application with `Application_Key__c` = that application's 18-character Id.
5. Retrieve: `sf project retrieve start --metadata CustomObject:Loan__c CustomTab:Loan__c`
6. Commit: `feat(data-model): Loan__c with Application_Key__c and encrypted payout account [LAMS-012]`.

## Learn

- **A lookup cannot be unique**, so a separate unique text field holding the parent Id enforces one-to-one. The 18-character Id is case-safe, so case sensitivity of the unique check does not matter in practice.
- **Classic encrypted text** (175 characters max) is masked unless the user has *View Encrypted Data* (granted to Operations in LAMS-027). It cannot be unique, an external ID, used in SOQL `WHERE`, report filters or formulas.
- **Formula (Text) buckets** stay correct whenever Days_Past_Due__c changes; the nightly batch only writes one number.
- Activities must be enabled on an object before Tasks can be related to its records (BR-36, BR-50).

## Done when

- [ ] Object and all 20 fields exist in the org and in source
- [ ] A test loan gets Name `LN-000001`-style, Status Pending Disbursement and Disbursement_Status Pending
- [ ] A second loan with the same Application_Key__c fails on the unique check
- [ ] Principal 3,00,000 with fee 6,000 shows Net_Disbursement__c ₹2,94,000
- [ ] Days_Past_Due__c 0 / 6 / 31 / 61 / 90 / 91 shows Current / Soft / Watch / Substandard / Substandard / Critical
- [ ] Payout_Account__c `123456789012` displays as `XXXXXXXX9012` for a user without View Encrypted Data
- [ ] BRD §10.5 / BR-49 updated with the day-90 boundary
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.5 Loan__c; §11 Apex managed sharing, FLS; Appendix #6; BR-29, BR-33 – BR-37, BR-49, BR-72
