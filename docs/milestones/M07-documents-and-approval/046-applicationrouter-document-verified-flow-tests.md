# LAMS-046 · ApplicationRouter + Document Verified flow + tests

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** M (2–5h) · **Delivers:** BR-19, §13.3

**Depends on:** LAMS-045 (documents get verified), LAMS-042 (KycService, to add the router call), LAMS-044 (Override Credit Score flow, to add the router call), LAMS-010 (Docs_Complete__c), LAMS-031 (Under Review needs Docs_Complete__c)

## Goal

One Apex router decides the next step only when **both** the mandatory documents are verified and eligibility has run; whichever arrives second triggers it (§13.3). This item builds the router with steps 1, 2 and 5 (status only) and the Document Verified flow, so every verified file moves to Under Review automatically (BR-19). Steps 3–5 are completed by LAMS-048 (approval submission), LAMS-049 (auto-approve) and LAMS-050 (Secured Loan Review).

## Build

**Class `ApplicationRouter`** — `public without sharing class` (it runs as the verifying officer, the submitter's queued job or the Automated Process user, and must route regardless; comment why).

```apex
@InvocableMethod(label='Route Application' category='LAMS')
public static void route(List<Id> applicationIds);          // from flows

public static void routeApplications(Set<Id> applicationIds);  // from Apex (KycService)

public class RoutingException extends Exception {}
```

**Routing steps** (§13.3), applied to records queried `FOR UPDATE` with Status__c, Docs_Complete__c, Eligibility_Run_Date__c, Eligibility_Result__c, Amount__c, Risk_Grade__c, OwnerId, Borrower__r.KYC_Status__c, Loan_Product__r.Product_Code__c, Loan_Product__r.Requires_Field_Verification__c

| Step | Condition | Action | Built in |
| --- | --- | --- | --- |
| 0 | Status__c ≠ Document Review | Skip — already routed; makes the router idempotent when the last document and the score arrive together | this item |
| 1 | Docs_Complete__c false **or** Eligibility_Run_Date__c blank | Stop | this item |
| 2 | Borrower KYC_Status__c = Rejected | Status = Rejected, Rejection_Reason__c = KYC Failed, Decision_Comments__c = label `LAMS_Router_KYC_Rejected`, Decision_Date__c = today | this item |
| 3 | Product Requires_Field_Verification__c and Secured_Review_Enabled__c | Start Secured Loan Review | LAMS-050 (until then, falls through to 5) |
| 4 | Auto-approve conditions (BR-27) and Auto_Approve_Enabled__c | Approved, offer issued | LAMS-049 |
| 5 | Otherwise | Status = Under Review; submit to Loan Approval | Status here; submission in LAMS-048 |

- One `Database.update(records, false)` for all routed records; collect failures and throw one `RoutingException` listing the record Ids and messages (not swallowed; a flow fault path or the async job error log shows it).
- Toggles only through FeatureToggle (LAMS-019).
- Keep each step a private method (`isKycRejected`, `needsSecuredReview`, `isAutoApprove`, `submitForApproval`) so LAMS-048–050 only fill them in.

**Flow `Document_Verified`** — label *Document Verified*, Record-Triggered on **Application_Document__c**, **A record is updated**, condition `Status__c Equals Verified`, **Only when a record is updated to meet the condition requirements**, Actions and Related Records. It triggers on the child record, not on the Docs_Complete__c formula (§13.2).

| Path | Element |
| --- | --- |
| **Run Asynchronously** path (proposed) | Action *Route Application* with `{!$Record.Loan_Application__c}` (the master-detail field from LAMS-010) |

Why the asynchronous path: the parent's roll-up summaries (Mandatory_Docs_Verified__c, hence Docs_Complete__c) are recalculated *after* the child's after-save flows in the same save. Routing in the immediate path would read a stale Docs_Complete__c and the Under Review validation rule would fail. The asynchronous path runs after commit, when the roll-up is current.

**Wire the other arrival point**

- `KycService.execute` and `KycService.retry` (LAMS-042): after `EligibilityService.evaluate(ids)` call `ApplicationRouter.routeApplications(ids)`.
- `Override_Credit_Score` flow (LAMS-044): element 7 *Route Application* after *Run Eligibility* (the BRD only says the override calls EligibilityService; without this a file whose documents were already complete would never move — proposed).

## Steps

1. `sf apex generate class --name ApplicationRouter --output-dir force-app/main/default/classes` and `ApplicationRouterTest`.
2. Build the router with steps 0, 1, 2, 5 and stubs for 3 and 4.
3. Build the Document Verified flow with the asynchronous path; add the router call to KycService and the Override Credit Score flow.
4. Retrieve and deploy: `sf project retrieve start --metadata Flow:Document_Verified Flow:Override_Credit_Score`, then `sf project deploy start --source-dir force-app/main/default`.
5. `sf apex run test --class-names ApplicationRouterTest KycServiceTest --code-coverage --result-format human --wait 10`
6. Manual: verify the last mandatory document on a scored application → refresh after a few seconds → Under Review.
7. Commit: `feat(apex): ApplicationRouter and Document Verified flow [LAMS-046]`.

## Learn

- **Record-triggered flow on the child vs a formula on the parent:** formulas are computed on read and never "change", so a flow cannot trigger on Docs_Complete__c; trigger on the document whose status really changed.
- **Order of execution:** roll-up summaries on the master are recalculated after the child's after-save automation — hence the asynchronous path.
- **Two arrival points, one decision:** both the last document and the score call the same router, and the Status = Document Review guard plus `FOR UPDATE` make a double call harmless.
- Asynchronous paths run in their own transaction (separate limits, and a different running user is possible — FeatureToggle's org defaults make that safe, C3).

## Done when

- [ ] Docs complete + eligibility run → Status Under Review
- [ ] Only docs complete, or only eligibility run → no change; the later arrival routes it (test both orders: verify last doc then KYC job, and KYC job then verify last doc)
- [ ] Optional documents do not block routing; an application with zero mandatory items never routes
- [ ] KYC Rejected → Rejected with reason KYC Failed, comment and Decision_Date__c
- [ ] Calling the router twice for the same record changes nothing the second time
- [ ] Bulk: 200 applications routed in one call, 1 DML; verifying 200 last documents in one update routes all 200 (assert after `Test.stopTest()`, which runs the asynchronous path)
- [ ] A forced DML failure raises `RoutingException` with the record Id
- [ ] Override Credit Score on a file with all documents verified moves it to Under Review
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-11, BR-13, BR-19, §10.3 Docs\_Complete\_\_c, Eligibility\_Run\_Date\_\_c, §13.1 Under Review rule, §13.2 Document Verified, Override Credit Score, §13.3 Routing logic, §14 ApplicationRouter, KycService, C3, appendix item 4
