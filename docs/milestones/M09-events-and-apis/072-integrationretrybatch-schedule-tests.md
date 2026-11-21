# LAMS-072 · IntegrationRetryBatch + schedule + tests

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** M (2–5h) · **Delivers:** BR-66

**Depends on:** LAMS-039 (IntegrationLogger, `IntegrationRetryable`), LAMS-018 (`Max_Retries__c` per integration), LAMS-041 (CreditBureauService), LAMS-042 (KycService), LAMS-056 (PayoutService), LAMS-063 (SmsService), LAMS-067 (CoreBankingSyncQueueable)

## Goal

A failed outbound call is retried automatically every hour until it succeeds or reaches the integration's `Max_Retries__c`, then is marked **Gave Up** and the owner gets a Task (BR-66, NFR-04, NFR-08). This is the milestone exit check "a failed call retries to Gave Up".

## Build

**Class** `public without sharing class IntegrationRetryBatch implements Database.Batchable<SObject>, Database.AllowsCallouts, Schedulable` (system job; it must see every log regardless of owner).

| Part | Spec |
| --- | --- |
| `start` | `SELECT Id, Integration__c, Related_Record_Id__c, Retry_Count__c, Request__c, Status__c FROM Integration_Log__c WHERE Direction__c = 'Outbound' AND Status__c IN ('Failed','Retrying') AND Next_Retry_At__c <= :System.now()` |
| Scope | **1** — each retry is its own transaction, so the service can do callout → DML → enqueue its next job exactly as in its normal path |
| `execute` | Look up the handler, skip if its toggle is off, call `retry(log)`, apply the state rules below, update the log |
| `finish` | Nothing (the next hourly run picks up what is due) |
| `execute(SchedulableContext)` | `Database.executeBatch(new IntegrationRetryBatch(), 1);` |
| Schedule | `System.schedule('LAMS Integration Retry Hourly', '0 0 * * * ?', new IntegrationRetryBatch());` |

**Handler lookup** (proposed: a private static map in the batch; `Type.forName(className).newInstance()` cast to `IntegrationRetryable`, so each service needs a public no-arg constructor):

| Integration__c | Class | Integration_Setting__mdt | Skip when |
| --- | --- | --- | --- |
| Credit Bureau | CreditBureauService | Credit_Bureau | – |
| KYC | KycService | KYC | – |
| Payout | PayoutService | Payout | – |
| SMS | SmsService | SMS | `SMS_Enabled__c` off |
| Core Banking | CoreBankingSyncQueueable | Core_Banking | `Core_Banking_Sync_Enabled__c` off |

Inbound logs (Partner API, Payment Callback, Loan Status SOAP) are never retried.

**`retry(Integration_Log__c log)` contract** (all five services): rebuild the request from `Related_Record_Id__c` (the stored `Request__c` is masked), send it, run the service's normal success/failure DML, and write the outcome on the passed log (`Status__c` Success or Failed, `HTTP_Status__c`, `Response__c`, `Duration_Ms__c`). It does not insert a new log row; one row tracks one logical call.

**State rules** (proposed back-off; `Max_Retries__c` from the integration's metadata record):

| After the attempt | Status__c | Retry_Count__c | Next_Retry_At__c | Extra |
| --- | --- | --- | --- | --- |
| Success | Success | +1 | blank | – |
| Failed, count < Max | Retrying | +1 | now + 2^count hours (2 h after retry 1, 4 h after retry 2; the first retry is due 1 h after the original failure, set by IntegrationLogger) | – |
| Failed, count = Max | **Gave Up** | +1 | blank | Task (below) |
| `retry` throws | as Failed | +1 | as above | Exception message in `Response__c` |

**Gave Up Task:** OwnerId = owner of the related record (Loan__c → `Assigned_Officer__c`; Loan_Application__c → `OwnerId`; otherwise the job's running user); WhatId = `Related_Record_Id__c`; Subject = label `LAMS_Task_Integration_Gave_Up` (proposed) + integration name; Priority High; ActivityDate today. For Credit Bureau this is the officer's prompt to use Override Credit Score (BR-15, LAMS-044).

**Running user:** the user who schedules the job (an admin) must hold External Credential principal access for all five credentials (LAMS-040).

## Steps

1. Write `IntegrationRetryBatch`; confirm each of the five services implements `IntegrationRetryable` with a no-arg constructor (fix them in this branch if not).
2. Write `IntegrationRetryBatchTest` with `Test.setMock(HttpCalloutMock.class, …)` (and `WebServiceMock` for KYC):
   - Due Failed log + mock 503 → Retrying, count 1, Next_Retry_At ≈ now + 2 h.
   - Log at count = Max − 1 + mock 503 → Gave Up, Task to the right owner.
   - Mock 200 → Success, business effect done (e.g. loan Active for Payout).
   - Not yet due, Inbound, Success and Gave Up logs → untouched.
   - Core Banking log with the toggle off → untouched.
   - Bulk: insert 200 due logs and assert `start()` returns 200 rows; run one `execute()` (in a test only one scope runs).
   - Schedulable: `System.schedule` inside `Test.startTest()`, assert a `CronTrigger` row.
3. Deploy; schedule the job with an anonymous script `scripts/apex/schedule-jobs.apex` (proposed) and add it to the post-deploy notes, because scheduled jobs are not metadata:
   `sf apex run --file scripts/apex/schedule-jobs.apex`
4. Exit demo: submit an application whose PAN ends in 9 (bureau mock returns 503, §16), run the batch by hand `Database.executeBatch(new IntegrationRetryBatch(), 1);` (set `Next_Retry_At__c` to now between runs), and watch the log go Failed → Retrying → Gave Up:
   `sf data query -q "SELECT Integration__c, Status__c, Retry_Count__c, Next_Retry_At__c FROM Integration_Log__c ORDER BY CreatedDate DESC LIMIT 5"`
5. Commit: `feat(apex): IntegrationRetryBatch hourly retry to Gave Up [LAMS-072]`.

## Learn

- **Batch + callouts:** a batch that calls out needs `Database.AllowsCallouts`; each `execute` has its own limits (100 callouts, callouts before DML), which is why scope 1 keeps the services' normal flow intact.
- **Interfaces + `Type.forName`** let one job retry any service without a hardcoded `if/else` on class names spread through the code.
- A class referenced by a scheduled job cannot be redeployed while the job is queued unless *Allow deployments of components when corresponding Apex jobs are pending or in progress* is on (Deployment Settings).
- Never replay a masked request body; rebuild from the source record so PAN and account numbers stay out of the log (BR-65).

## Done when

- [ ] Exit criterion: a bureau failure (PAN ending 9) goes Failed → Retrying → Gave Up after `Max_Retries__c` attempts and a Task reaches the application owner
- [ ] A retry that succeeds sets Success and completes the business step (e.g. payout activates the loan, AC-08 retry path)
- [ ] The hourly job appears in Setup → Scheduled Jobs, and the schedule script is in source
- [ ] `IntegrationRetryBatchTest` passes with ≥ 90% coverage, using callout mocks, a toggle-off case and the 200-row `start()` case
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §14 IntegrationRetryBatch, IntegrationRetryable, callout rule; §10.9 Integration_Log__c (Retrying, Gave Up, Next_Retry_At__c); §10.11 Max_Retries__c; §16 mock behaviour; BR-15, BR-65, BR-66, NFR-04, NFR-08, AC-08
