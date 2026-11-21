# LAMS-067 · CoreBankingSyncQueueable + LoanEventTrigger + PaymentChangeEventTrigger + tests

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** L (5–10h) · **Delivers:** BR-38, BR-47

**Depends on:** LAMS-014 (Loan_Event__e, CDC on Loan__c and Payment__c), LAMS-018 (Integration_Setting__mdt `Core_Banking`), LAMS-019 (FeatureToggle), LAMS-036 (LoanEventPublisher), LAMS-039 (IntegrationLogger, IntegrationRetryable), LAMS-040 (Named + External Credential `Core_Banking`), LAMS-056 (PayoutService publishes *Loan Disbursed*), LAMS-058 (PaymentTrigger inserts/reverses payments)

## Goal

Every disbursement and every payment is posted to core banking without slowing the user who caused it (BR-38, BR-47): disbursements arrive through the `Loan_Event__e` stream, payments through Change Data Capture, and both are sent by one queueable that logs each call (BR-65) and can be retried (BR-66).

## Build

**Flow of control**

```
PayoutService → LoanEventPublisher → Loan_Event__e (Loan Disbursed) → LoanEventTrigger ┐
Payment__c insert / Status change → Payment__ChangeEvent → PaymentChangeEventTrigger  ├→ CoreBankingSyncQueueable → callout:Core_Banking
                                                                                        ┘
```

**Trigger `LoanEventTrigger`** on `Loan_Event__e` (after insert), logic in `LoanEventTriggerHandler`:

| Rule | Detail |
| --- | --- |
| Filter | Only `Event_Type__c = 'Loan Disbursed'`; collect `Record_Id__c` (loan Ids) |
| Toggle | Do nothing when `FeatureToggle` says `Core_Banking_Sync_Enabled__c` is off (loans keep `Core_Banking_Sync_Status__c = Pending`) |
| Enqueue | One `System.enqueueJob(new CoreBankingSyncQueueable(loanIds, new Set<Id>()))` per trigger batch, never one per event |
| Checkpoint | `EventBus.TriggerContext.currentContext().setResumeCheckpoint(lastEvent.ReplayId)` after processing, so a failure resumes from there |

**Trigger `PaymentChangeEventTrigger`** on `Payment__ChangeEvent` (after insert), logic in `PaymentChangeEventHandler`:

| Rule | Detail |
| --- | --- |
| Header | `EventBus.ChangeEventHeader h = event.ChangeEventHeader;` one event can carry several `h.getRecordIds()` |
| Which changes | `CREATE` → sync; `UPDATE` only when `h.getChangedFields()` contains `Status__c` (e.g. Reversed); `DELETE`/`UNDELETE` → ignore; `GAP_*` → sync the record Ids (re-read the payment) |
| Toggle / enqueue | Same as above: one job with the payment Ids |

**Running user (proposed).** Both triggers run as the Automated Process user by default, and the callout needs External Credential principal access for `Core_Banking`. Add a `PlatformEventSubscriberConfig` for each trigger (`LoanEventTriggerConfig`, `PaymentChangeEventTriggerConfig`, batch size 200) whose user holds the permission set with `Core_Banking` principal access (the Integration User is proposed). The username is org-specific: record it in the README.

**Class `CoreBankingSyncQueueable`** — `public with sharing class CoreBankingSyncQueueable implements Queueable, Database.AllowsCallouts, IntegrationRetryable`

| Member | Signature / rule |
| --- | --- |
| Constructors | `CoreBankingSyncQueueable()` (no-arg, needed by IntegrationRetryBatch `Type.newInstance`) and `CoreBankingSyncQueueable(Set<Id> loanIds, Set<Id> paymentIds)` |
| `execute(QueueableContext)` | 1) query loans and payments; 2) all callouts; 3) DML; 4) `IntegrationLogger` flush; 5) if more than 100 records were passed, enqueue a new job with the rest (100-callout limit) |
| `retry(Integration_Log__c log)` | Re-reads the record in `Related_Record_Id__c` (Loan__c or Payment__c by key prefix), rebuilds the request, sends it and writes the outcome on the passed log (`Status__c`, `HTTP_Status__c`, `Response__c`, `Duration_Ms__c`); no new log row (LAMS-072) |
| Endpoint | `callout:Core_Banking` + `Path__c` from `Integration_Setting__mdt.Core_Banking` + `/disbursements` or `/payments` (sub-paths proposed); timeout = `Timeout_Ms__c` |

Requests (JSON, proposed shape):

```json
POST …/disbursements  {"loanNumber":"LN-000045","principal":1000000,"netDisbursed":980000,"utr":"UTR26112100045","disbursementDate":"2026-11-21"}
POST …/payments       {"loanNumber":"LN-000045","reference":"PG-20261121-0001","amount":8979,"paymentDate":"2026-12-21","mode":"Online","status":"Success"}
```

| Response | Result |
| --- | --- |
| 200 / 201 | Log `Success`; disbursement → `Loan__c.Core_Banking_Sync_Status__c = Synced` |
| 4xx, 5xx, timeout, `CalloutException` | Log `Failed` with `Next_Retry_At__c` (LAMS-039 rule); disbursement → `Core_Banking_Sync_Status__c = Failed` |

Payments have no sync-status field in the BRD; the `Integration_Log__c` row (Related_Record_Id__c = payment Id, Integration__c = Core Banking) is the sync record. Do **not** update `Payment__c` from the queueable: it is locked after insert (LAMS-032) and an update would fire another change event.

Logging: Integration__c `Core Banking`, Direction__c `Outbound`, one log per record sent; no account numbers in the request.

**Test classes:** `CoreBankingSyncQueueableTest`, `LoanEventTriggerTest`, `PaymentChangeEventTriggerTest` with an `HttpCalloutMock` (`CoreBankingMock`, proposed) that returns 200 or 503 by loan number.

## Steps

1. Confirm in Setup → Change Data Capture that `Loan__c` and `Payment__c` are selected (LAMS-014); check `force-app/.../platformEventChannelMembers/ChangeEvents_Payment_ChangeEvent.platformEventChannelMember-meta.xml` is in source.
2. Configure the Core Banking mock (LAMS-006): `POST /disbursements` and `/payments` return 201; a loan number ending in 9 returns 503 (proposed rule).
3. Write `CoreBankingSyncQueueable` (callouts first, DML after, logger flush last).
4. Write the two triggers with handlers; keep each trigger one line calling its handler.
5. Write the tests:
   - Queueable: 200 response → Synced + Success log; 503 → Failed + log with Next_Retry_At; 150 records → exactly 100 callouts and the rest handed to a chained job (chained jobs cannot run in a test: guard the enqueue with `Test.isRunningTest()` or assert through a test-visible flag); toggle off → no callout.
   - `LoanEventTriggerTest`: publish Loan Disbursed and Loan Overdue events, `Test.getEventBus().deliver()`, assert one queueable job for the Disbursed loan only.
   - `PaymentChangeEventTriggerTest`: `Test.enableChangeDataCapture()`, insert 200 payments, `Test.getEventBus().deliver()`, assert exactly one `CoreBankingSyncQueueable` job in `AsyncApexJob` (not 200); an update that does not touch `Status__c` enqueues nothing.
6. Create the `PlatformEventSubscriberConfig` records, deploy, and test end to end: disburse a demo loan, see `Synced`; post a payment via Postman (LAMS-070), see a Core Banking log row.
7. `sf project deploy start --metadata ApexClass ApexTrigger PlatformEventSubscriberConfig` then `sf apex run test --class-names CoreBankingSyncQueueableTest LoanEventTriggerTest PaymentChangeEventTriggerTest --code-coverage --result-format human`
8. Commit: `feat(apex): core banking sync via platform event and CDC triggers [LAMS-067]`.

## Learn

- **CDC entity selection:** change events are only published for objects selected in Setup → Change Data Capture (or a `PlatformEventChannelMember` on `ChangeEvents`); the trigger object is `Payment__ChangeEvent`, and fields arrive only when changed.
- **Event and change-event triggers run as the Automated Process user** with up to 2,000 events per batch. `PlatformEventSubscriberConfig` changes the running user and batch size; per-user settings and per-user credentials otherwise do not apply (BRD C3).
- **Callouts are not allowed directly in triggers**; enqueue a Queueable with `Database.AllowsCallouts` once per batch.
- Apex tests do not see real events: use `Test.enableChangeDataCapture()` and `Test.getEventBus().deliver()`.

## Done when

- [ ] A disbursed loan reaches `Core_Banking_Sync_Status__c = Synced` with a `Success` Core Banking log row (BR-38)
- [ ] A new payment and a reversal each produce a Core Banking log row (BR-47); a non-status update does not
- [ ] With `Core_Banking_Sync_Enabled__c` off nothing is sent and loans stay `Pending`
- [ ] A 503 from the mock leaves a `Failed` log with `Next_Retry_At__c` set, ready for LAMS-072
- [ ] All three test classes pass with ≥ 90% coverage on the queueable and both handlers, including the 200-record CDC bulk test (one job, not 200)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §14 CoreBankingSyncQueueable, LoanEventTrigger, PaymentChangeEventTrigger, callout rule; §16 Core Banking row; §10.5 Core_Banking_Sync_Status__c and CDC; §10.9; §10.10; §8 C2, C3; BR-38, BR-47, BR-65, BR-66
