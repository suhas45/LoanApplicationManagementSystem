# LAMS-041 · CreditBureauService + HttpCalloutMock tests

**Milestone:** [M06 – Origination](README.md) · **Size:** L (5–10h) · **Delivers:** BR-10

**Depends on:** LAMS-039 (IntegrationLogger, IntegrationRetryable), LAMS-040 (Credit_Bureau credential), LAMS-038 (Application Submitted flow, to add the action), LAMS-018 (Credit_Bureau metadata record), LAMS-019 (FeatureToggle), LAMS-006 (mock PAN conventions)

## Goal

After submission the credit score is fetched asynchronously from the bureau (or the in-org mock) and saved on the application (BR-10), with every call logged (BR-65). A failed call leaves the score blank and is retried (BR-66); after the last retry the application is flagged for a manual score (BR-15). KYC always follows in the chain (§14).

## Build

**Class `CreditBureauService`** — `public without sharing class CreditBureauService implements Queueable, Database.AllowsCallouts, IntegrationRetryable`. `without sharing` because it runs as whoever submitted (possibly a portal borrower, who has no edit on Credit_Score__c); say so in a class comment.

```apex
public CreditBureauService();                       // no-arg: IntegrationRetryBatch creates it by name
public CreditBureauService(Set<Id> applicationIds);

@InvocableMethod(label='Request Credit Score' category='LAMS')
public static void enqueue(List<Id> applicationIds);   // chunks of 50 → one job each

public void execute(QueueableContext ctx);
public void retry(Integration_Log__c failedLog);         // IntegrationRetryable
public static void flagForManualOverride(Set<Id> applicationIds);
```

**`enqueue`** splits the Ids into chunks of 50 (proposed `CHUNK_SIZE`; stays under 100 callouts per transaction, C2) and calls `System.enqueueJob` once per chunk — 200 submissions → 4 jobs, inside the 50-jobs-per-transaction limit.

**`execute` — callouts first, then DML, then chain**

| Phase | Work |
| --- | --- |
| 1 Read | Settings by SOQL: `SELECT Named_Credential__c, Path__c, Timeout_Ms__c, Max_Retries__c, Mock_Response__c FROM Integration_Setting__mdt WHERE DeveloperName = 'Credit_Bureau'` (`getInstance()` truncates the Long Text Mock_Response__c to 255 characters). Applications `WHERE Id IN :ids AND Credit_Score__c = null` with Borrower__r PAN__c, FirstName, LastName, Birthdate |
| 2 Call | For each application: `IntegrationLogger.start('Credit_Bureau', 'Outbound', app.Id)`. If `FeatureToggle.isMockMode('Credit_Bureau')` (Bureau_Mock_Mode__c) → no callout, parse Mock_Response__c (proposed meaning of mock mode; see below). Otherwise `POST 'callout:' + Named_Credential__c + Path__c`, timeout = Timeout_Ms__c, JSON body below |
| 3 Parse | 200 with an integer `score` 300–900 → `IntegrationLogger.success(...)`; anything else (non-200, timeout, `CalloutException`, bad JSON, score out of range) → `IntegrationLogger.failure(...)` (Status Failed, Next_Retry_At__c = now + 1 h) |
| 4 DML | One update: Credit_Score__c, Credit_Score_Source__c = Bureau for the successes |
| 5 Log | `IntegrationLogger.flush()` |
| 6 Chain | `System.enqueueJob(new KycService(allIds))` (LAMS-042) — for successes **and** failures; KYC does not need the score, and EligibilityService refuses to run without it (AC-04). Guard with `if (!Test.isRunningTest())` and set `@TestVisible static Boolean kycEnqueued = true` so tests can assert it |

**Request / response** (must match the LAMS-006 mock)

```json
POST {Path__c}   { "pan": "ABCDE1234F", "firstName": "…", "lastName": "…",
                   "dateOfBirth": "1990-01-31", "correlationId": "<log Correlation_Id__c>" }
200              { "score": 790, "reportId": "CB-000123" }
```

Mock behaviour is driven by the **9th character of the PAN** (its last digit, LAMS-006): `9` → 503 (failure and retry demo, §16); `8` → 200 with score 685 (Refer on a 700 product); any other → 200 with a passing score. Seed borrowers in LAMS-016 follow this.

**Mock mode (proposed meaning):** Bureau_Mock_Mode__c on → no callout; the score comes from Mock_Response__c (e.g. `{"score":790,"reportId":"MOCK"}`) and the call is still logged as Success. Off → real callout through the Named Credential, which points at the public mock. Switch it off to demo AC-04 and AC-05 with the delayed and 503 responses.

**`retry(failedLog)`** (IntegrationRetryable contract, LAMS-039)

1. Rebuild the request from `failedLog.Related_Record_Id__c` (the application) — never from Request__c, which is masked.
2. Same call, parse and update as phases 2–5 for that one application.
3. Record the attempt on the **same** row: `IntegrationLogger.retried(failedLog, ...)` → Success, or Retrying with Next_Retry_At__c = now + 2^n hours; then flush.
4. Success → enqueue `KycService` for that application (one log per transaction, so one enqueue is allowed even from the batch).
5. Failure and `Retry_Count__c ≥ Max_Retries__c` → `flagForManualOverride` for that application. IntegrationRetryBatch (LAMS-072) then marks the row Gave Up.

**`flagForManualOverride(applicationIds)`** — "flags the application for manual override" (§14): one Task per application, `OwnerId` = application owner, `WhatId` = application, Subject = label `LAMS_Task_Manual_Score_Needed` ("Credit bureau unavailable – enter a manual score"), ActivityDate = today, Priority High. Skips applications that already have an open Task with that subject.

**Flow change:** add element 8 *Request Credit Score* (this invocable) to `Application_Submitted` (LAMS-038), after the status update.

**Tests `CreditBureauServiceTest`** with a `CreditBureauHttpMock implements HttpCalloutMock` (`@IsTest` class; constructor takes status code and body, or a flag to throw `CalloutException`). Build data with TestDataFactory using the PAN conventions above.

## Steps

1. `sf apex generate class --name CreditBureauService --output-dir force-app/main/default/classes`; also `CreditBureauHttpMock` and `CreditBureauServiceTest`.
2. Write a stub `KycService` with the no-arg and `Set<Id>` constructors so this compiles (LAMS-043 comes next, then LAMS-042 replaces the stub).
3. Write the service and tests. In tests insert data **before** `Test.startTest()`, set the mock, then run the job inside start/stop.
4. Add the *Request Credit Score* action to the Application Submitted flow; save a new version.
5. `sf project deploy start --source-dir force-app/main/default`
6. `sf apex run test --class-names CreditBureauServiceTest --code-coverage --result-format human --wait 10`
7. Manual, mock mode off: submit for a borrower with PAN `ABCDE1239F` → Failed log with Next_Retry_At__c; PAN `ABCDE1238F` → score 685; PAN `ABCDE1234F` → passing score.
8. Commit: `feat(apex): CreditBureauService queueable with logging and retry [LAMS-041]`.

## Learn

- **Queueable + `Database.AllowsCallouts`:** a record save cannot call out, so the flow enqueues a job that runs after commit.
- **Order inside the job:** all callouts, then DML, then `flush()`, then enqueue — any DML before a callout raises "uncommitted work pending".
- **Chaining limits:** a running queueable may enqueue only one child; Developer Edition caps chain depth (5); chaining from a queueable inside a test throws, hence the `Test.isRunningTest()` guard.
- **HttpCalloutMock:** tests can never call out; `Test.setMock(HttpCalloutMock.class, mock)` returns your canned response, and a test that sets no mock fails on a callout — which also proves mock mode really skips it.

## Done when

- [ ] 200 OK → Credit_Score__c and Credit_Score_Source__c = Bureau saved; one Success log (Integration__c = Credit_Bureau) with Correlation_Id__c, HTTP_Status__c 200, Duration_Ms__c, and the PAN masked in Request__c
- [ ] 503, `CalloutException` and malformed JSON each → score blank, Failed log with Next_Retry_At__c, no exception escapes the job
- [ ] Mock mode on → no callout (test sets no mock and still passes), score from Mock_Response__c read by SOQL; mock mode off → callout made
- [ ] KYC is enqueued after both success and failure (`kycEnqueued`)
- [ ] `enqueue` with 200 Ids → 4 jobs (`Limits.getQueueableJobs()`); a 50-record job uses 1 DML for applications and 1 for logs
- [ ] `retry` success saves the score and sets the same log row to Success; failure sets Retrying, increments Retry_Count__c and pushes Next_Retry_At__c out by 2^n hours; the service has a public no-arg constructor
- [ ] Final failed retry (Retry_Count__c reaches Max_Retries__c) creates one High-priority Task for the application owner, and no duplicate on a second call (first half of **AC-05**; completed in LAMS-044)
- [ ] Application Submitted flow enqueues the job (flow test: `Limits.getQueueableJobs()` = 1 after submit)
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-10, BR-15, BR-65, BR-66, BR-69, §10.9, §10.11, §12 Bureau\_Mock\_Mode\_\_c, §14 corrected origination chain, callout rule, CreditBureauService, IntegrationRetryBatch, §16 Credit Bureau and mock behaviour, C2, NFR-03, NFR-04, AC-04, AC-05
