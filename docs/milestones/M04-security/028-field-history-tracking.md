# LAMS-028 · Field History Tracking

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-73

**Depends on:** M02 done (LAMS-009, LAMS-012)

## Goal

Every change to an application's status, amounts, eligibility and score source, and to a loan's status, disbursement status and assigned officer, is kept as history with who changed it and when (BR-73, O6). Officers and auditors can then see how each decision came about.

## Build

**Loan_Application__c**: enable *Track Field History* on the object.

| Field | Why |
| --- | --- |
| Status__c | BR-73 |
| Amount__c | BR-73 |
| Approved_Amount__c | BR-73, BR-25 (approver reductions) |
| Eligibility_Result__c | BR-73 |
| Credit_Score_Source__c | §11 Audit, BR-15 (manual overrides are audited) |
| Credit_Score__c (proposed) | BR-15: shows the old and new score when an override replaces a bureau score |

**Loan__c**: enable *Track Field History* on the object.

| Field | Why |
| --- | --- |
| Status__c | BR-73 |
| Disbursement_Status__c | BR-73 |
| Assigned_Officer__c | BR-73 (reassignment also moves the Apex share, LAMS-054) |

**Layouts:** add the *Loan Application History* related list to the 4 application layouts and *Loan History* to the Loan layout. Also add it to the Dynamic Forms Lightning pages from LAMS-015.

The other audit sources in §11 (approval history, Integration_Log__c, Setup Audit Trail) need no work here.

## Steps

1. Object Manager → Loan Application → Fields & Relationships → **Set History Tracking**. Tick *Enable Loan Application History* and the 6 fields.
2. Do the same on Loan for its 3 fields.
3. Add the History related lists to the layouts and pages.
4. Retrieve: `sf project retrieve start --metadata CustomObject:Loan_Application__c CustomObject:Loan__c Layout FlexiPage`. Check `<enableHistory>true</enableHistory>` on the objects and `<trackHistory>true</trackHistory>` on the 9 fields.
5. Check in the org: change an application's Amount__c in Draft. Then run `sf data query --query "SELECT Field, OldValue, NewValue, CreatedBy.Name FROM Loan_Application__History ORDER BY CreatedDate DESC LIMIT 5"`.
6. Commit: `feat(security): field history tracking on application and loan [LAMS-028]`.

## Learn

- **History lives in `<Object>__History`** (here `Loan_Application__History`, `Loan__History`). You can query it but not write to it, and each object can track up to 20 fields.
- **History rows are not created in Apex tests**, so you can't assert them in a test class. Check them in the org instead.
- **Retention:** field history is kept 18 months in the UI and 24 months through the API. NFR-07 asks for 7 years, which needs Field Audit Trail (Shield) or an archive job. Record this gap for the "archive policy decided before go-live" note.
- Long Text Area changes are tracked without old and new values, which is one reason Eligibility_Notes__c isn't tracked.

## Done when

- [ ] History tracking is on for Loan_Application__c (6 fields) and Loan__c (3 fields), in source and deployed
- [ ] Changing an application's Amount__c and Status__c creates two `Loan_Application__History` rows with old and new values
- [ ] The History related list shows on every application layout and on the Loan layout
- [ ] An Operations Officer can't see Credit_Score__c changes in History (FLS from LAMS-027 applies)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Audit, §7 NFR-07, §1 objective O6, BR-15, BR-25, BR-73
