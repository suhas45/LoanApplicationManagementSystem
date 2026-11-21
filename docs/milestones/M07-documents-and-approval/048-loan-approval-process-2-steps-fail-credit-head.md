# LAMS-048 · Loan Approval process (2 steps, Fail → Credit Head)

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** M (2–5h) · **Delivers:** BR-21 – BR-24

**Depends on:** LAMS-046 (router step 5), LAMS-047 (Application_Decided flow sends the decision emails), LAMS-022 (roles), LAMS-029 (test users), LAMS-031 (decision validation rules and their LAMS_VR_* labels)

## Goal

Every application the router sends to Under Review goes to the Credit Managers (BR-21) and, above Second_Approval_Threshold__c or when eligibility is Fail, also to the Credit Head (BR-22, BR-23). The approver can reduce the amount while the record is locked (BR-25); the creator can never approve (BR-24); Refer/Fail approvals and all rejections carry the required comments even though approval field updates skip validation rules (BR-23, BR-26).

## Build

**Queues** (proposed names; created here because the approval needs them before LAMS-078, which adds Case to the first one)

| Queue | Supported objects | Members |
| --- | --- | --- |
| `Credit_Managers` | Loan_Application__c | Role: Credit Manager |
| `Credit_Head` | Loan_Application__c | Role: Credit Head |

Members by role, so no user Ids are hardcoded. In the `Lams` org the only holder of the Credit Head role is the System Administrator, who acts as Credit Head (LAMS-029), so the admin is the `Credit_Head` queue's member and approves step 2. The Credit Manager (Salesforce Platform licence) can still approve: approvals on a custom object work on that licence.

**Approval process `Loan_Approval`** on Loan_Application__c

| Setting | Value |
| --- | --- |
| Entry criteria | `Status__c equals Under Review` |
| Initial submitters | Record Owner (the router submits on the owner's behalf) |
| Record editability | **Administrators OR the currently assigned approver can edit records during the approval process** (BR-25) |
| Approval page fields | Name, Loan_Product__c, Amount__c, Approved_Amount__c, Tenure__c, EMI__c, EMI_To_Income__c, LTV__c, Credit_Score__c, Credit_Score_Source__c, Risk_Grade__c, Eligibility_Result__c, Eligibility_Notes__c, Decision_Comments__c, Rejection_Reason__c |
| Initial submission actions | Record lock (default) |
| **Step 1** *Credit Manager Review* | All records enter; approver: queue `Credit_Managers`; reject → final rejection |
| **Step 2** *Credit Head Approval* | Criteria formula: `OR( BLANKVALUE(Approved_Amount__c, Amount__c) > $Setup.LAMS_Settings__c.Second_Approval_Threshold__c, ISPICKVAL(Eligibility_Result__c, 'Fail') )`; else → approve record. Approver: queue `Credit_Head`; reject → final rejection |
| Final approval actions | Field updates: Status__c = Approved; Decision_Date__c = `TODAY()`; Offer_Expiry_Date__c = `TODAY() + $Setup.LAMS_Settings__c.Offer_Validity_Days__c`. **Unlock** the record (the borrower must be able to accept, withdraw is allowed up to Approved) |
| Final rejection actions | Status__c = Rejected; Decision_Date__c = `TODAY()`; record stays locked |
| Recall actions | Status__c = Document Review; unlock |
| Email alerts | None here (proposed): `Application_Decided` (LAMS-047) emails on the status change in the borrower's language, which also covers auto-approve. §13.4 lists an email alert |

Loan Officers are in neither queue, so the creator can never approve (BR-24).

**Router step 5** (fill `submitForApproval` in ApplicationRouter, LAMS-046) — after the Under Review update:

```apex
Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
req.setObjectId(app.Id);
req.setProcessDefinitionNameOrId('Loan_Approval');
req.setSubmitterId(app.OwnerId);        // the Loan Officer, whoever runs the router
req.setComments(Label.LAMS_Router_Submitted_Comment);
// collect, then one call:
List<Approval.ProcessResult> results = Approval.process(requests, false);   // failures → RoutingException
```

**Decision guard — because approval field updates do not run validation rules.** The LAMS-031 rules (score and eligibility before Approved; Decision_Comments__c for Refer/Fail; Rejection_Reason__c on Rejected) would be skipped by the final approval/rejection field updates. Triggers *do* run on those updates, so add (proposed names):

- Trigger `LoanApplicationTrigger` (before update) → handler `ApplicationDecisionGuard.validate(List<Loan_Application__c> newList, Map<Id, Loan_Application__c> oldMap)`. One trigger for the object (NFR-09); later logic goes into the same handler class pattern.
- When Status__c changes to **Approved**: Credit_Score__c and Eligibility_Result__c must be set; if Eligibility_Result__c is Refer or Fail, Decision_Comments__c must be set (BR-23).
- When Status__c changes to **Rejected**: Rejection_Reason__c and Decision_Comments__c must be set (BR-26).
- Failure → `record.addError(Label.LAMS_VR_...)` using the LAMS-031 labels; the approver sees the message on Approve/Reject, fills the fields on the record (it is editable for them) and clicks again.
- The router (KYC Failed) and Secured Loan Review (Policy) always set reason and comment, so system rejections pass.

Approval page *Description* (step instructions, label text): "Before approving a Refer or Fail, or rejecting, fill Decision Comments (and Rejection Reason) on the record."

## Steps

1. Create the two queues (Setup → Queues); retrieve `Queue:Credit_Managers Queue:Credit_Head`.
2. Build `Loan_Approval` (Setup → Approval Processes → Loan Application → Use Standard Setup Wizard); activate.
3. Fill `submitForApproval` in ApplicationRouter.
4. `sf apex generate trigger --name LoanApplicationTrigger --sobject Loan_Application__c --event "before update" --output-dir force-app/main/default/triggers`; `sf apex generate class --name ApplicationDecisionGuard --output-dir force-app/main/default/classes`; tests `LoanApprovalProcessTest`, `ApplicationDecisionGuardTest`.
5. Retrieve: `sf project retrieve start --metadata ApprovalProcess:Loan_Application__c.Loan_Approval Queue:Credit_Managers Queue:Credit_Head`
6. Deploy and test: `sf project deploy start --source-dir force-app/main/default`, then `sf apex run test --class-names LoanApprovalProcessTest ApplicationDecisionGuardTest ApplicationRouterTest --code-coverage --result-format human --wait 10`
7. Commit: `feat(approval): Loan Approval 2-step process and decision guard [LAMS-048]`.

## Learn

- **Record locking:** submission locks the record; only the approver-edit setting lets the current approver reduce Approved_Amount__c (and the LAMS-031 "≤ Amount" rule still runs on that normal edit).
- **Approval field updates skip validation rules** (and do not re-run them), but they fire Apex triggers — so rules that must hold at decision time belong in a before-update trigger as well.
- **Step criteria are evaluated when the previous step is approved,** so a reduction made during step 1 is seen by step 2's formula; `$Setup` references read the current threshold with no deployment (BR-81).
- **Submitting from Apex:** `setSubmitterId` must be an allowed initial submitter (here the owner); approvals cannot be tested without real users in queues — create users with the roles in the test.

## Done when

- [ ] ₹10 lakh, Pass: router submits → pending work item for queue Credit_Managers; a Credit Manager approves → Approved, Decision_Date__c today, Offer_Expiry_Date__c today + 15, record unlocked, offer email sent (LAMS-047)
- [ ] ₹60 lakh: after the Credit Manager approves it is still pending, now with Credit_Head; the Credit Head approves → Approved (AC-03 approval part; full AC-03 in LAMS-050)
- [ ] Fail result at ₹5 lakh → goes to the Credit Head; Refer at ₹5 lakh → Credit Manager only
- [ ] Approving a Refer or Fail without Decision_Comments__c, or rejecting without Rejection_Reason__c and Decision_Comments__c, is blocked with the label message; with them it succeeds
- [ ] The Credit Manager can change Approved_Amount__c while locked; a Loan Officer cannot edit the record and cannot approve (`Approval.process` as the creator throws)
- [ ] Recall → Status Document Review, unlocked
- [ ] Bulk: 200 applications routed → 200 approval instances in one `Approval.process` call; guard handles 200 records
- [ ] Changing Second_Approval_Threshold__c to 50 lakh → the ₹60 lakh still needs the Credit Head, a ₹40 lakh does not
- [ ] Coverage ≥ 90% for ApplicationRouter, ApplicationDecisionGuard and the trigger
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-21, BR-22, BR-23, BR-24, BR-25, BR-26, BR-81, §4 approval authority, §12 Second\_Approval\_Threshold\_\_c, Offer\_Validity\_Days\_\_c, §13.1, §13.3 step 5, §13.4 Loan Approval, §13.5 Credit Managers queue, NFR-09, AC-03
