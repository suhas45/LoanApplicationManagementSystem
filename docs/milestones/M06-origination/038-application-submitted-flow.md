# LAMS-038 · Application Submitted flow

**Milestone:** [M06 – Origination](README.md) · **Size:** M (2–5h) · **Delivers:** BR-09, BR-16

**Depends on:** LAMS-035 (sets Status = Submitted), LAMS-036 (LoanEventPublisher), LAMS-037 (OwnerAssignmentService), LAMS-010 (Application_Document__c), LAMS-016 (product checklists seeded), LAMS-026 (Private OWD, so AC-06 is meaningful)

## Goal

At submission the rate is fixed (BR-09), the dates are stamped, portal and partner applications get a Loan Officer (BR-07), the document checklist is created from the product (BR-16), the status moves to Document Review and an Application Submitted event is published (BR-68). It does **not** run eligibility (§13.2). Completes **AC-06**.

## Build

**Flow `Application_Submitted`** — label *Application Submitted*, Record-Triggered, object Loan_Application__c, **A record is created or updated**, condition `Status__c Equals Submitted`, **Only when a record is updated to meet the condition requirements**, optimised for **Actions and Related Records** (after save). Created is included because the partner API (LAMS-069) may insert an application already Submitted.

| # | Element | Details |
| --- | --- | --- |
| 1 | Decision *Needs owner?* | `{!$Record.Channel__c}` = Portal **or** Partner API → 2; Branch → 3 |
| 2 | Action *Assign Officer* (OwnerAssignmentService) | Inputs mode = `Application`, recordId = `{!$Record.Id}`; store `assignedUserId` in `varNewOwnerId` |
| 3 | Get Records *Checklist* | Product_Document__c where `Loan_Product__c = {!$Record.Loan_Product__c}`, all records |
| 4 | Loop over checklist → Assignment | Add a new Application_Document__c to `colDocuments`: master field = `{!$Record.Id}`, Document_Type__c, Mandatory__c copied, Status__c = Requested |
| 5 | Create Records | `colDocuments` (one DML, after the loop) |
| 6 | Update Records *$Record* | Interest_Rate__c = `{!$Record.Loan_Product__r.Interest_Rate__c}`; Submitted_Date__c = `{!$Flow.CurrentDateTime}`; Last_Activity_Date__c = `{!$Flow.CurrentDateTime}`; Status__c = Document Review; OwnerId = `varNewOwnerId` when not blank (formula resource `BLANKVALUE(varNewOwnerId, $Record.OwnerId)`) |
| 7 | Action *Publish Loan Event* (LoanEventPublisher) | eventType `Application Submitted`, recordId `{!$Record.Id}`, amount `{!$Record.Amount__c}` |
| 8 | Action *Request Credit Score* | Added in LAMS-041 (enqueues CreditBureauService) |
| 9 | Submitted email | Added in LAMS-047 |
| 10a | *Campaign from membership* (BR-88, AC-18, proposed) | Added in **LAMS-099**, before element 10. When `{!$Record.Campaign__c}` is blank, it takes the borrower's most recent non-Applied membership of an **active** campaign and sets Campaign__c from it, so a pre-approved borrower's portal or branch application carries the campaign. Element 10 then uses `varCampaignId` = `BLANKVALUE($Record.Campaign__c, <found campaign>)`. Leave it out until then |
| 10 | *Campaign Applied* (BR-88, v2.2) | Added when **LAMS-099** is built (M14), because it needs `Loan_Application__c.Campaign__c`, which LAMS-099 creates. Decision `{!$Record.Campaign__c}` is not blank → Get Records CampaignMember where CampaignId = `{!$Record.Campaign__c}` and ContactId = `{!$Record.Borrower__c}` (the individual's Contact, or the director) → Update Records Status = Applied. If no member exists, create one with Status Applied (proposed). Leave it out until then |

**Errors:** leave elements 2, 5 and 6 without fault connectors on purpose. An unhandled fault rolls back the whole save, so the user's Submit fails with the message instead of leaving a half-submitted record; the platform's flow error email reaches the admin. Elements **10a and 10 are the exception, by design** (LAMS-099): each has a fault connector to the end, because campaign bookkeeping (for example a campaign without an *Applied* member status) must never roll back a submission.

**Rules this must respect**

- Element 6 changes Status to Document Review, so the entry condition is no longer met and the flow does not run again for the same record.
- The BR-08 lock rule (LAMS-031) must allow the system to change Status/Interest_Rate__c/OwnerId; only Product, Amount, Tenure are locked.
- The portal borrower keeps access after the owner changes, through the sharing set (Borrower__c = User.ContactId, LAMS-077).

**Test class `ApplicationSubmittedFlowTest`** (record-triggered flows run inside Apex tests): use TestDataFactory (§14; first built for LAMS-033 — add methods as needed) for products with checklists, borrowers and Draft applications.

## Steps

1. Build the flow in Flow Builder; use `$Record.Loan_Product__r` directly instead of an extra Get Records for the rate.
2. Activate; submit a Branch and a Portal application by hand and check the checklist and owner.
3. Write `ApplicationSubmittedFlowTest` (`sf apex generate class --name ApplicationSubmittedFlowTest --output-dir force-app/main/default/classes`).
4. Retrieve and deploy: `sf project retrieve start --metadata Flow:Application_Submitted`, then `sf project deploy start --source-dir force-app/main/default`.
5. `sf apex run test --class-names ApplicationSubmittedFlowTest --code-coverage --result-format human --wait 10`
6. Commit: `feat(flow): Application Submitted flow with owner assignment and checklist [LAMS-038]`.

## Learn

- **After-save vs before-save:** stamping fields on `$Record` is cheapest before save, but calling Apex and creating child records needs after save; here one after-save update keeps it simple.
- **"Only when updated to meet the condition"** stops re-entry when the flow updates its own record.
- **Flow bulkification:** with 200 records the platform batches the Create Records and Apex action across interviews — but only if DML stays outside loops.
- **Owner change and sharing:** changing OwnerId drops the old owner's implicit access; portal users keep theirs through the sharing set, managers gain it through the role hierarchy (AC-06).
- **Campaign members after conversion:** when a lead converts, its CampaignMember rows get the new ContactId, so element 10 finds the member by Borrower__c even though the borrower started as a lead.

## Done when

- [ ] Submitting a Personal Loan sets Interest_Rate__c = 14, Submitted_Date__c and Last_Activity_Date__c = now, Status = Document Review, and one Application_Document__c per product checklist row with Status Requested and Mandatory copied
- [ ] Branch application keeps its owner; Portal and Partner API applications are owned by the least-loaded Loan Officer
- [ ] **AC-06:** test as a portal borrower: create and submit an application (Channel Portal) → owner is a Loan Officer; `System.runAs(creditManager)` query `WITH USER_MODE` finds it; another Loan Officer cannot see it
- [ ] Bulk: 200 applications updated to Submitted in one DML → 200 × checklist rows created, no limit errors
- [ ] An event is published with Event_Publishing_Enabled__c on and none when off
- [ ] Changing a Document Review record again does not re-run the flow (no duplicate checklist)
- [ ] Coverage ≥ 90% for any Apex touched; flow test passes
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-07, BR-08, BR-09, BR-16, BR-68, BR-70, BR-88, §5 statuses, §11 Owner assignment and sharing, §13.2 Application Submitted, §13.6 Campaign Applied, §14 corrected origination chain, AC-06, AC-18
