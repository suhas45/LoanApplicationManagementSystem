# LAMS-052 · Respond to Offer + Withdraw Application flows

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** M (2–5h) · **Delivers:** BR-29, BR-32

**Depends on:** LAMS-048 (Loan_Approval recall action, record unlocked after approval), LAMS-051 (offer letter to show), LAMS-031 (Withdrawal_Reason__c rule), LAMS-027 (borrowers have no FLS edit on Status__c), LAMS-009 (field added below)

## Goal

The borrower accepts or declines the offer (an officer may record the answer for them) (BR-29), and an application can be withdrawn with a reason from Draft up to Approved, recalling any pending approval (BR-32). Both are guided screens because borrowers can never edit Status__c directly.

## Build

**New field (proposed, not in §10.3):** `Loan_Application__c.Decline_Reason__c` — Text(255). The BRD asks for a decline reason but has no field for it; Decision_Comments__c belongs to the approver. Add it to LAMS-009's metadata and the BRD.

**Flow `Respond_to_Offer`** — label *Respond to Offer*, Screen Flow, input `recordId`, run **System Context With Sharing – Enforces Record-Level Access** (writes Status__c for borrowers who lack FLS edit; sharing still limits them to their own applications).

| # | Element | Details |
| --- | --- | --- |
| 1 | Get Records | Loan_Application__c by recordId (Name, Status__c, Approved_Amount__c, Interest_Rate__c, Tenure__c, EMI__c, Offer_Expiry_Date__c) |
| 2 | Decision *Offer open?* | Status__c = Approved **and** Offer_Expiry_Date__c ≥ `{!$Flow.CurrentDate}` → 3; otherwise screen *Offer not available* (label `LAMS_Offer_Not_Available`) |
| 3 | Screen *Your offer* | Offer summary; link to the OfferLetter file (Get Records on ContentDocumentLink for the record, latest Title starting with the offer-letter label); radio *Accept* / *Decline*; `Decline reason` text (required, visible when Decline); for internal users (`{!$User.ContactId}` blank) a required checkbox "Borrower confirmed this answer" (label; proposed) |
| 4a | Update (Accept) | Status__c = Offer Accepted, Offer_Accepted_Date__c = now, Last_Activity_Date__c = now. The Offer Accepted flow (LAMS-053) then creates the loan |
| 4b | Update (Decline) | Status__c = Offer Declined, Decline_Reason__c, Last_Activity_Date__c = now |
| 5 | Screen *Done* | Confirmation label |

**Flow `Withdraw_Application`** — label *Withdraw Application*, Screen Flow, input `recordId`, same run mode.

| # | Element | Details |
| --- | --- | --- |
| 1 | Get Records | Loan_Application__c by recordId |
| 2 | Decision *Can withdraw?* | Status__c in Draft, Submitted, Document Review, Under Review, Approved → 3; otherwise screen *Cannot withdraw* (label) |
| 3 | Screen *Reason* | Withdrawal reason (required) + confirm checkbox |
| 4 | Action *Recall Pending Approval* | Only when Status__c = Under Review: `ApprovalRecallService` (below). The recall action sets Status back to Document Review and unlocks |
| 5 | Update Records | Status__c = Withdrawn, Withdrawal_Reason__c, Last_Activity_Date__c = now |
| 6 | Screen *Done* | Confirmation |

Fault connectors on every update/action → error screen with `{!$Flow.FaultMessage}`.

**Class `ApprovalRecallService`** (proposed name) — `public without sharing class` (a borrower is not the submitter, so the recall runs in system mode; it only ever recalls `Loan_Approval` items for the Ids passed in).

```apex
@InvocableMethod(label='Recall Pending Approval' category='LAMS')
public static void recall(List<Id> applicationIds);
// SELECT Id FROM ProcessInstanceWorkitem
//  WHERE ProcessInstance.TargetObjectId IN :ids AND ProcessInstance.Status = 'Pending'
// for each: Approval.ProcessWorkitemRequest r; r.setWorkitemId(w.Id);
//           r.setAction('Removed'); r.setComments(Label.LAMS_Withdraw_Recall_Comment);
// Approval.process(requests, false); any failure → throw new RecallException(<ids + messages>)
public class RecallException extends Exception {}   // reaches the flow's fault path
```

**Placement:** quick actions *Respond to Offer* and *Withdraw Application* on Loan_Application__c, with Dynamic Actions visibility (Respond: Status = Approved; Withdraw: Status in the five allowed values). Portal buttons on *My Applications* come in LAMS-076; Portal_Enabled__c off behaviour in LAMS-079.

**Known limit:** withdrawing while a Secured Loan Review is running leaves its open work items; cancel the orchestration run from the Orchestration Runs list and log it in the milestone Parking lot (no BRD rule yet).

## Steps

1. Add `Decline_Reason__c` (LAMS-009 metadata, FLS for staff read and portal read).
2. `sf apex generate class --name ApprovalRecallService --output-dir force-app/main/default/classes` and `ApprovalRecallServiceTest`.
3. Build both flows and their labels; create the quick actions and Dynamic Actions filters.
4. Retrieve: `sf project retrieve start --metadata Flow:Respond_to_Offer Flow:Withdraw_Application QuickAction:Loan_Application__c.Respond_to_Offer QuickAction:Loan_Application__c.Withdraw_Application CustomField:Loan_Application__c.Decline_Reason__c FlexiPage`
5. `sf apex run test --class-names ApprovalRecallServiceTest --code-coverage --result-format human --wait 10`
6. Test both flows as a Loan Officer and as a portal borrower (Experience Builder preview or Login As).
7. Commit: `feat(flow): Respond to Offer and Withdraw Application [LAMS-052]`.

## Learn

- **Guided status changes:** removing FLS edit on Status__c and exposing only screen flows in *System Context With Sharing* makes every status change go through checked paths, while record sharing still protects other borrowers' data.
- **Recalling an approval from Apex** is `ProcessWorkitemRequest` with action `Removed`; the approval's recall actions still fire (Status → Document Review), so set Withdrawn afterwards.
- **Locked records:** the approval unlocks on final approval (LAMS-048), otherwise the borrower's Accept would fail on a locked record.

## Done when

- [ ] Borrower accepts an open offer → Offer Accepted, Offer_Accepted_Date__c set; declines → Offer Declined with Decline_Reason__c; Last_Activity_Date__c stamped both ways
- [ ] An expired offer (Offer_Expiry_Date__c yesterday) or a non-Approved application shows *Offer not available*
- [ ] A Loan Officer can record the answer for the borrower only after ticking the confirmation
- [ ] Withdraw from Draft, Document Review and Approved → Withdrawn with reason; from Under Review the pending approval is recalled first (no pending work item left); from Rejected or Offer Accepted it is refused
- [ ] A portal borrower cannot run either flow against another borrower's application (record not found)
- [ ] `ApprovalRecallServiceTest`: recalls 200 pending approvals in one call; no-op for records without one; coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-29, BR-30, BR-32, BR-59, §5 statuses (Offer Declined, Withdrawn), §10.3 Offer\_Accepted\_Date\_\_c, Withdrawal\_Reason\_\_c, Last\_Activity\_Date\_\_c, §13.1 withdrawal rule, §13.2 Respond to Offer, Withdraw Application, §13.4 recall, §15 portal My Applications
