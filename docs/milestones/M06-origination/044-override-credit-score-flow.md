# LAMS-044 · Override Credit Score flow

**Milestone:** [M06 – Origination](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-15

**Depends on:** LAMS-043 (EligibilityService), LAMS-041 (manual-score Task after the bureau gives up), LAMS-024 (custom permission LAMS_Override_Credit_Check), LAMS-031 (Override_Reason__c and "no approval without score" rules), LAMS-028 (history on Credit_Score_Source__c)

## Goal

When the bureau is still unavailable after all retries, only a user with override authority can enter a manual score with a reason; the override is flagged and audited, and eligibility then runs on it (BR-15). Completes **AC-05**.

## Build

**Flow `Override_Credit_Score`** — label *Override Credit Score*, Screen Flow, input `recordId` (Loan_Application__c). Runs in user context: only users with edit on Credit_Score__c (LAMS_Credit) can save, which is a second guard after the permission check.

| # | Element | Details |
| --- | --- | --- |
| 1 | Decision *Allowed?* | `{!$Permission.LAMS_Override_Credit_Check}` is false → screen *Not allowed* (label `LAMS_Override_No_Permission`) and end. This is the real check; the button visibility below is only convenience |
| 2 | Get Records | Loan_Application__c by recordId (Name, Status__c, Credit_Score__c, Credit_Score_Source__c) |
| 3 | Decision *Score already from bureau?* | Credit_Score_Source__c = Bureau → screen *Bureau score exists* and end (proposed: overrides are only for a missing bureau score) |
| 4 | Screen *Manual score* | Number `Score` (required, validation `AND({!Score} >= 300, {!Score} <= 900)`, label `LAMS_Override_Score`); Long Text `Reason` (required, label `LAMS_Override_Reason`) |
| 5 | Update Records | Credit_Score__c = Score, Credit_Score_Source__c = Manual Override, Override_Reason__c = Reason, Last_Activity_Date__c = `{!$Flow.CurrentDateTime}` |
| 6 | Action *Run Eligibility* (EligibilityService) | applicationId = recordId; keep `eligibilityResult` |
| 7 | Action *Route Application* | Added in LAMS-046 (so a file whose documents are already complete moves on) |
| 8 | Screen *Result* | Shows the eligibility result and notes |

Fault connectors on 5 and 6 → error screen with `{!$Flow.FaultMessage}`.

**Quick action** `Loan_Application__c.Override_Credit_Score` (Flow action). On the Lightning record pages use **Dynamic Actions** visibility: custom permission `LAMS_Override_Credit_Check` **and** Credit_Score__c is blank.

**Audit:** Credit_Score_Source__c history (LAMS-028) shows who switched to Manual Override and when; Override_Reason__c keeps the why. The Origination dashboard counts manual overrides later (LAMS-081).

**AC-05 test `OverrideCreditScoreTest`** (screen flows cannot run in Apex, so the test covers what the flow does):

- User A: Credit Manager role **without** the custom permission; User B: with it. §11 puts LAMS_Override_Credit_Check inside LAMS_Credit, which every Credit Manager gets, so in the test give User A only a test-created permission set with the Credit object access and User B the same plus a `SetupEntityAccess` row for the custom permission (proposed; log the BRD question in the milestone Parking lot).
- `System.runAs(A)`: `FeatureManagement.checkPermission('LAMS_Override_Credit_Check')` is false; updating the application to Approved with no score fails the LAMS-031 rule.
- `System.runAs(B)`: set score, source Manual Override and reason, then `EligibilityService.run(...)` → result and Eligibility_Run_Date__c set; source Manual Override with a blank reason fails validation.

## Steps

1. Build the flow; create the labels.
2. Create the quick action and add it to the application record pages with the Dynamic Actions filters.
3. Write `OverrideCreditScoreTest` (`sf apex generate class --name OverrideCreditScoreTest --output-dir force-app/main/default/classes`).
4. Retrieve: `sf project retrieve start --metadata Flow:Override_Credit_Score QuickAction:Loan_Application__c.Override_Credit_Score FlexiPage`
5. `sf apex run test --class-names OverrideCreditScoreTest --code-coverage --result-format human --wait 10`
6. Demo AC-05 end to end: Bureau mock mode off, borrower PAN with last digit 9 (e.g. `ABCDE1239F`) → Failed log; call `new CreditBureauService().retry(log)` from Anonymous Apex until Retry_Count__c reaches Max_Retries__c (LAMS-072 automates this later) → manual-score Task appears → log in as each Credit Manager.
7. Commit: `feat(flow): Override Credit Score with permission check [LAMS-044]`.

## Learn

- **`$Permission` in flows** reads custom permissions directly; checking inside the flow protects against the action being launched some other way (URL, another page).
- **Dynamic Actions** show or hide a button by permission and field value without separate page layouts.
- **Audit by design:** a separate source field plus history tracking makes overrides reportable, instead of hiding them in a comment.

## Done when

- [ ] A Credit Manager without LAMS_Override_Credit_Check does not see the action, and the flow ends at *Not allowed* if opened anyway
- [ ] A user with the permission enters 705 with a reason → Credit_Score_Source__c = Manual Override, reason saved, eligibility result and Eligibility_Run_Date__c set
- [ ] Score 250 or blank reason cannot be saved
- [ ] Field history shows the source change with user and time
- [ ] **AC-05:** with the bureau down after all retries, the user without override authority cannot approve (no score → validation blocks Approved) and the user with it can enter a manual score with a reason — `OverrideCreditScoreTest` passes
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-15, BR-11, §10.3 Credit\_Score\_Source\_\_c, Override\_Reason\_\_c, §11 custom permissions and audit, §13.1 override and approval rules, §13.2 Override Credit Score, §14 CreditBureauService, AC-05
