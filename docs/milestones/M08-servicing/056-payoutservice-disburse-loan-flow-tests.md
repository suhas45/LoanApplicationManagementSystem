# LAMS-056 · PayoutService + Disburse Loan flow + tests

**Milestone:** [M08 – Servicing](README.md) · **Size:** L (5–10h) · **Delivers:** BR-34 – BR-37

**Depends on:** LAMS-053 (loan in Pending Disbursement), LAMS-054 (assigned officer can edit the loan), LAMS-055 (EmiScheduleService; the schedule must exist before a loan can turn Active), LAMS-039 (IntegrationLogger, IntegrationRetryable), LAMS-040 (Named Credential `Payout_Service`), LAMS-036 (LoanEventPublisher), LAMS-019 (FeatureToggle)

## Goal

An Operations Officer confirms the payout account and triggers the payout. The screen returns at once, and an async job either activates the loan with its EMI schedule or marks it Failed with a task, ready for a retry (BR-34 – BR-37, AC-08).

## Build

**Screen flow `Disburse_Loan`** (label *Disburse Loan*). It is launched by quick action `Loan__c.Disburse_Loan`, which shows on the Loan Lightning page through Dynamic Actions only when `Status__c` = Pending Disbursement and `Disbursement_Status__c` is Pending or Failed.

1. Get the loan (`recordId`) with `Loan_Product__r.Product_Code__c`, `Loan_Application__r.Dealer_Name__c`, Principal__c, Processing_Fee_Amount__c, Net_Disbursement__c.
2. Decision: if the status is not as above, show an error screen (custom label) and finish.
3. **Screen 1 *Confirm payout*:** read-only Principal, Processing fee, **Net disbursement** (BR-35). The payee label is "Dealer account – {Dealer_Name__c}" when the product is AL, otherwise "Borrower account" (BR-34). Show the current Payout_Account__c masked. Inputs: Payout account (required) and Re-enter account (must match; validate on the screen). Checkbox "I confirm the amount and account" (required).
4. **Update Records** loan: `Payout_Account__c`, `Disbursement_Status__c` = In Progress.
5. **Apex action** `PayoutService` → *Request Payout* with the loan Id.
6. **Screen 2:** custom label `LAMS_Payout_Requested` ("Payout requested. The loan becomes Active when the payout service confirms."). The flow never waits for the result (§13.2).

**Class `PayoutService`** — `public with sharing class PayoutService implements Queueable, Database.AllowsCallouts, IntegrationRetryable`.

| Member | Signature |
| --- | --- |
| Invocable | `@InvocableMethod(label='Request Payout') public static void requestPayout(List<Id> loanIds)` → `System.enqueueJob(new PayoutService(loanIds))` |
| Constructor | `public PayoutService(List<Id> loanIds)` |
| Queueable | `public void execute(QueueableContext ctx)` |
| Retry | `public void retry(Integration_Log__c log)` (from LAMS-039) re-sends for `Related_Record_Id__c` when the loan is still Failed or In Progress |
| Finalizer | inner class `PayoutFinalizer implements Finalizer` attached in `execute` |

`execute`, all callouts first and DML last (§14 callout rule):

1. Query the loans in `loanIds` with `Disbursement_Status__c = 'In Progress'`. Skipping others prevents a double payout. Take at most 100, because each loan is one callout. Chain any remaining Ids in a new `PayoutService` job at the end.
2. Read `Integration_Setting__mdt` `Payout` (Named_Credential__c, Path__c, Timeout_Ms__c, Mock_Response__c).
3. For each loan, build `{"loanNumber": Name, "amount": Net_Disbursement__c, "account": Payout_Account__c, "payeeType": "Dealer"|"Borrower", "correlationId": <uuid>}`.
   - **Payout_Mock_Mode__c on** (FeatureToggle): parse `Mock_Response__c` and make no HTTP call. A payout account ending in 9 returns a failure instead (proposed, following the §16 "ends in 9" convention), so both paths can be demoed.
   - **Off:** `POST callout:Payout_Service` + Path__c, timeout Timeout_Ms__c, header `Idempotency-Key: <loan Name>`.
   - Success = HTTP 200 and `status = "SUCCESS"` with `utr`. Anything else, including a `CalloutException`, is a failure.
   - Buffer one IntegrationLogger row per call (Integration__c = Payout, Direction Outbound, Related_Record_Id__c = loan Id, Correlation_Id__c, HTTP status, duration). The account number is masked by the logger (BR-65, BR-72).
4. DML, after the callouts:

| Outcome | Loan__c updates | Also |
| --- | --- | --- |
| Success | `Disbursement_Status__c` = Disbursed, `Disbursement_Reference__c` = UTR, `Disbursement_Date__c` = today, `Status__c` = Active | `EmiScheduleService.createSchedules(successIds)` (BR-37); `LoanEventPublisher` publishes *Loan Disbursed* for each (BR-38, consumed in M09) |
| Failure | `Disbursement_Status__c` = Failed; `Status__c` stays Pending Disbursement | Task: OwnerId = Assigned_Officer__c, WhatId = loan, Subject = label `LAMS_Task_Payout_Failed` (proposed), Priority High, ActivityDate today, Description = error (BR-36) |

5. Flush the IntegrationLogger buffer (one insert).
6. **Finalizer:** if the job ends with an unhandled exception, set the loans still In Progress to Failed and create the same Task, so no loan is left In Progress forever (NFR-08).

**Retries (BR-36):** manually, the officer runs Disburse Loan again (allowed while Failed). Automatically, IntegrationRetryBatch calls `retry()` in M09 (BR-66).

## Steps

1. Write `PayoutService`. Add the labels `LAMS_Payout_Requested` and `LAMS_Task_Payout_Failed` with Hindi translations.
2. Build `Disburse_Loan`. Create the quick action and add it with visibility filters to the Loan record page (LAMS-015).
3. Write `PayoutMock implements HttpCalloutMock` (proposed) that returns 200 + UTR, or 503, depending on a constructor flag.
4. Write `PayoutServiceTest`:
   - **AC-08 failure:** mock 503 → loan Pending Disbursement, Disbursement_Status Failed, exactly 1 Task owned by Assigned_Officer__c, 1 Integration_Log__c Failed
   - **AC-08 retry:** set In Progress again, mock 200 → Active, Disbursed, UTR saved, Disbursement_Date today, 12 EMI rows
   - Toggle: Payout_Mock_Mode__c on with no HttpCalloutMock set → succeeds (proves no callout); off → uses the mock HTTP response
   - A loan not In Progress is ignored (no callout, no change)
   - Bulk: 200 loans in mock mode → 200 Active, 2,400 EMI rows
   - Finalizer: force an exception with a `@TestVisible static Boolean forceError` flag → loan Failed + Task
5. `sf apex run test --class-names PayoutServiceTest --code-coverage --result-format human --wait 10`
6. Demo in the org: as an Operations Officer, disburse a loan with a payout account ending in 9 (fails), check the Task, then run Disburse Loan again with a correct account (succeeds, schedule appears).
7. Retrieve: `sf project retrieve start --metadata Flow:Disburse_Loan QuickAction:Loan__c.Disburse_Loan ApexClass:PayoutService ApexClass:PayoutServiceTest ApexClass:PayoutMock`
8. Commit: `feat(servicing): PayoutService and Disburse Loan flow [LAMS-056]`.

## Learn

- **A screen flow cannot wait on a queueable.** The job runs after the screen's transaction commits. The flow sets In Progress and tells the user; the queueable writes the outcome (BRD appendix #3).
- **Callouts before DML:** a callout after uncommitted DML in the same transaction throws `CalloutException: You have uncommitted work pending`. Collect results, then update, then buffer-flush logs.
- **Limits per async transaction:** 100 callouts and 120 seconds total callout time. That is why one job handles at most 100 loans and why Timeout_Ms__c should be short.
- **Transaction Finalizers** (`System.attachFinalizer`) run even when the queueable fails, which makes them the place to undo an "In Progress" flag. The `Idempotency-Key` stops a retry after a timeout from paying twice.

## Done when

- [ ] AC-08: a payout failure leaves the loan Pending Disbursement with Disbursement_Status Failed and creates one Task for the assigned officer; a retry that succeeds sets Active and creates the EMI schedule
- [ ] Disburse Loan shows Net_Disbursement__c = Principal − fee and asks for the dealer account on an Auto loan
- [ ] The UTR is stored in Disbursement_Reference__c; every call has an Integration_Log__c row with the account masked
- [ ] With Payout_Mock_Mode__c on, no HTTP call is made; with it off, the Named Credential is used
- [ ] The quick action is hidden once the loan is Active or In Progress
- [ ] `PayoutServiceTest` passes (failure, retry, toggle on/off, bulk 200, finalizer) with ≥ 90% coverage
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.6 BR-34 – BR-38, §9 AC-08, §10.5 Loan__c disbursement fields, §10.11 Integration_Setting__mdt, §12 Payout_Mock_Mode__c, §13.2 Disburse Loan, §14 PayoutService and callout rule, §16 Payout Service, BR-65, BR-66, BR-72, NFR-08
