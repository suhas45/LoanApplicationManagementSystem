# LAMS-009 · Loan_Application__c fields, 4 record types, picklists

**Milestone:** [M02 – Data model](README.md) · **Size:** L (5–10h) · **Delivers:** §10.3

**Depends on:** LAMS-007 (Loan_Product__c), LAMS-008 (Contact borrower fields)

## Goal

The central object of the lifecycle exists: one application per borrower and product (BR-01), carrying its status through every stage in §5, the credit and decision fields, and the product-specific details captured per record type (BR-05). Formulas (LAMS-011), the document roll-ups (LAMS-010) and validation rules (M05) are added on top of these fields.

## Build

**Object `Loan_Application__c`** — label *Loan Application*, plural *Loan Applications*; Name = Auto Number `LA-{000000}` starting at 1; enable Reports, Activities (approval reminders and tasks), Track Field History (fields chosen in LAMS-028), Search, Bulk API and Streaming API. OWD is set in LAMS-026.

**Fields** (formula and roll-up fields from §10.3 are built in LAMS-010 and LAMS-011, not here)

| Field (API name) | Type | Details |
| --- | --- | --- |
| Borrower__c | Lookup(Contact) | Required; delete behaviour *Don't allow deletion*; child relationship `Loan_Applications`, related list *Loan Applications* |
| Loan_Product__c | Lookup(Loan_Product__c) | Required; *Don't allow deletion*; lookup filter `Loan_Product__c.Active__c = true` (proposed); child relationship `Loan_Applications` |
| Amount__c | Currency(16,2) | Required (proposed: the live EMI and BR-03 need it even on a draft) |
| Tenure__c | Number(3,0) | Required (proposed). Months |
| Purpose__c | Picklist (restricted) | Values per record type, below. **Proposed change:** §10.3 says Text Area, but per-record-type values only work on a picklist |
| Channel__c | Picklist (restricted) | Branch (default), Portal, Partner API |
| Status__c | Picklist (restricted) | Draft (default), Submitted, Document Review, Under Review, Approved, Rejected, Offer Accepted, Offer Declined, Withdrawn, Expired |
| Interest_Rate__c | Percent(3,2) | Copied from the product on submit (BR-09) |
| Credit_Score__c | Number(3,0) | |
| Credit_Score_Source__c | Picklist (restricted) | Bureau, Manual Override (BR-15) |
| Override_Reason__c | Text Area(255) | Required by validation when source = Manual Override (LAMS-031) |
| Eligibility_Result__c | Picklist (restricted) | Pass, Refer, Fail |
| Eligibility_Notes__c | Long Text Area(32768), 5 lines | Each breached rule |
| Eligibility_Run_Date__c | Date/Time | Blank until the score arrives (BR-11) |
| Approved_Amount__c | Currency(16,2) | ≤ Amount__c (validation in LAMS-031, BR-25) |
| Rejection_Reason__c | Picklist (restricted) | Low Credit Score, High EMI-to-Income, Insufficient Income, Incomplete Documents, Policy, KYC Failed, Other |
| Decision_Comments__c | Text Area(255) | |
| Withdrawal_Reason__c | Text(255) | BR-32 |
| Submitted_Date__c | Date/Time | |
| Decision_Date__c | Date | |
| Offer_Accepted_Date__c | Date/Time | |
| Offer_Expiry_Date__c | Date | Stamped at approval; not a formula (§10.3) |
| Last_Activity_Date__c | Date/Time | Stamped by user actions only; drives 30-day expiry (BR-31) |
| External_Reference__c | Text(50) | Unique (case-insensitive), External ID. Partner idempotency key (BR-06) |
| Partner_Name__c | Text(80) | |
| Property_Value__c | Currency(16,2) | Home |
| Vehicle_Price__c | Currency(16,2) | Auto |
| Dealer_Name__c | Text(80) | Auto |
| GST_Number__c | Text(15) | Business (GSTIN is 15 characters) |
| Annual_Turnover__c | Currency(16,2) | Business |
| Field_Verification_Status__c | Picklist (restricted) | Pending, Cleared, Failed |
| AI_Summary__c | Long Text Area(32768), 10 lines | Written by the Loan Officer Assistant (LAMS-086) |

**Record types** — DeveloperNames must match `Loan_Product__c.Record_Type_Name__c` from LAMS-007.

| DeveloperName | Label | Purpose__c values (proposed) |
| --- | --- | --- |
| Personal | Personal | Medical, Education, Wedding, Travel, Home Renovation, Debt Consolidation, Other |
| Home | Home | Home Purchase, Construction, Plot Purchase, Balance Transfer, Home Improvement, Other |
| Auto | Auto | New Car, Used Car, Two-Wheeler, Commercial Vehicle, Other |
| Business | Business | Working Capital, Equipment Purchase, Business Expansion, Inventory, Other |

All other picklists show all values in every record type. Make the four record types available to System Administrator now (default: Personal); the LAMS profiles get them in LAMS-023. Assign the default page layout to all four for now; per-record-type layouts come in LAMS-015.

**Also:** a tab for Loan_Application__c (so you can test now; LAMS-015 adds it to the LAMS app), and an *All* list view showing Name, Borrower, Product, Status, Amount, Channel.

## Steps

1. Create the object with the auto-number Name.
2. Create the two lookups first, then the other fields. For long picklists, writing `.field-meta.xml` is faster than the UI. Example for Status__c:
   ```xml
   <valueSet>
       <restricted>true</restricted>
       <valueSetDefinition>
           <sorted>false</sorted>
           <value><fullName>Draft</fullName><default>true</default><label>Draft</label></value>
           <value><fullName>Submitted</fullName><default>false</default><label>Submitted</label></value>
           <!-- … the other eight values in BRD order … -->
       </valueSetDefinition>
   </valueSet>
   ```
3. Create the four record types, then set the Purpose__c values on each (Record Type → Picklists Available for Editing → Purpose → Edit).
4. Create the tab and list view.
5. Retrieve: `sf project retrieve start --metadata CustomObject:Loan_Application__c CustomTab:Loan_Application__c`
   Check that `objects/Loan_Application__c/recordTypes/` holds four files with `picklistValues` for Purpose__c.
6. Deploy check: `sf project deploy start --dry-run --source-dir force-app`.
7. Commit: `feat(data-model): Loan_Application__c fields and record types [LAMS-009]`.

## Learn

- **Record types filter picklist values**, not field visibility. Field visibility per type comes from page layouts and Dynamic Forms (LAMS-015).
- **Required lookups** cannot use "Clear the value of this field" on delete, so a borrower or product with applications cannot be deleted.
- **Auto Number Name** fields give readable IDs (`LA-000001`) but are not reset when records are deleted; set the start number before loading data.
- Adding a picklist value later does not add it to existing record types unless you tick "Add the new picklist values to all record types" (or edit the record type XML).

## Done when

- [ ] All 32 custom fields above and four record types exist in the org and in source
- [ ] A new Personal application gets Name `LA-000001`-style, Status Draft, Channel Branch, and Purpose offers only the Personal values
- [ ] A Home application offers only the Home Purpose values
- [ ] A second application with the same External_Reference__c fails on the unique check
- [ ] An inactive product cannot be selected; a Contact with an application cannot be deleted
- [ ] `sf project deploy start --dry-run --source-dir force-app` succeeds
- [ ] BRD §10.3 updated: Purpose__c type is Picklist
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.3 Loan_Application__c; §5 Application statuses; §21 Record types; BR-01, BR-05, BR-06, BR-09, BR-11, BR-15, BR-25, BR-26, BR-31, BR-32
