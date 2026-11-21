# LAMS-039 · IntegrationLogger + IntegrationRetryable interface + tests

**Milestone:** [M06 – Origination](README.md) · **Size:** M (2–5h) · **Delivers:** BR-65

**Depends on:** LAMS-014 (Integration_Log__c), LAMS-018 (Integration_Setting__mdt.Max_Retries__c). Must be done before LAMS-041 and LAMS-042 (milestone order note).

## Goal

Every inbound and outbound call writes one Integration_Log__c row with status, duration and a correlation ID, with PAN and account numbers masked (BR-65). Rows are buffered and inserted once after the callouts, so logging never causes "uncommitted work pending" (§14 callout rule). Every outbound service implements one retry contract (BR-66).

## Build

**Class `IntegrationLogger`** — `public without sharing class` (logs must be written whatever the running user can see; Integration_Log__c is Private, §11).

```apex
public static Integration_Log__c start(String integration, String direction, Id relatedRecordId);
public static void success(Integration_Log__c log, Integer httpStatus, String request, String response);
public static void failure(Integration_Log__c log, Integer httpStatus, String request, String response);
public static void retried(Integration_Log__c existingLog, Boolean succeeded, Integer httpStatus,
                           String request, String response);
public static void flush();
public static String mask(String text);
@TestVisible private static List<Integration_Log__c> buffer;
```

| Method | Does |
| --- | --- |
| `start` | Builds an in-memory row: Integration__c (picklist API name, same as the Integration_Setting__mdt DeveloperName: `Credit_Bureau`, `KYC`, `Payout`, `SMS`, `Core_Banking`; inbound APIs use their own values), Direction__c (`Outbound` / `Inbound`, proposed values), Related_Record_Id__c, Correlation_Id__c = `UUID.randomUUID().toString()`, Retry_Count__c = 0; records the start time (`System.now().getTime()`) in a private map. Adds the row to the buffer and returns it, so the caller can send the correlation Id in the request |
| `success` | Status__c = Success, HTTP_Status__c, Request__c / Response__c = `mask(...)` truncated to the field length, Duration_Ms__c = now − start |
| `failure` | Same fields, Status__c = Failed, Next_Retry_At__c = now + 2^0 = 1 hour (IntegrationRetryBatch runs hourly, LAMS-072) |
| `retried` | Updates the **same** row (it is already in the database, so it is buffered for update): Retry_Count__c + 1; on success Status__c = Success and Next_Retry_At__c cleared; on failure Status__c = Retrying and Next_Retry_At__c = now + 2^Retry_Count__c hours (2 h, 4 h, …). Marking **Gave Up** after Max_Retries__c is IntegrationRetryBatch's job (§14) |
| `flush` | One `Database.upsert(buffer, false)` (new rows insert, retried rows update), errors to `System.debug(LoggingLevel.ERROR, …)`, then clears the buffer. No-op when the buffer is empty |
| `mask` | PAN pattern `[A-Z]{5}[0-9]{4}[A-Z]` → `XXXXXX` + last 4 (e.g. `XXXXXX234F`); runs of 9–18 digits (account numbers) → `X…` + last 4. Null-safe |

Status flow (values from §10.9): **Failed** (first failure) → **Retrying** (a retry failed, retries left) → **Gave Up** (set by LAMS-072 after Max_Retries__c), or → **Success** at any point.

**Interface `IntegrationRetryable`**

```apex
public interface IntegrationRetryable {
    // Rebuilds the request from failedLog.Related_Record_Id__c (Request__c is masked,
    // so it can never be resent as is), makes the call, then records the attempt on the
    // SAME log row with IntegrationLogger.retried(...) and flushes.
    void retry(Integration_Log__c failedLog);
}
```

Contract for implementers:

- A **public no-argument constructor**, because IntegrationRetryBatch creates the service by name: `(IntegrationRetryable) Type.forName(className).newInstance()`.
- One log per transaction: the batch runs with scope 1 (LAMS-072), so `retry` may do its callout, then its DML, then flush.
- Never create a new log row for a retry; the batch reads the updated Status__c and Retry_Count__c from the same row.

**Usage pattern every service follows**

```apex
Integration_Log__c log = IntegrationLogger.start('Credit_Bureau', 'Outbound', app.Id);
// ... all callouts first ...
IntegrationLogger.success(log, res.getStatusCode(), req.getBody(), res.getBody());
// ... then business DML ...
IntegrationLogger.flush();   // last
```

## Steps

1. `sf apex generate class --name IntegrationLogger --output-dir force-app/main/default/classes`; create `IntegrationRetryable.cls` (interface) and `IntegrationLoggerTest`.
2. Write the tests with a private fake `IntegrationRetryable` implementation inside the test class.
3. `sf project deploy start --source-dir force-app/main/default/classes`
4. `sf apex run test --class-names IntegrationLoggerTest --code-coverage --result-format human --wait 10`
5. Commit: `feat(apex): IntegrationLogger and IntegrationRetryable [LAMS-039]`.

## Learn

- **Callout after uncommitted DML:** once a transaction has done DML, a callout throws `CalloutException: You have uncommitted work pending`. Buffering log rows and inserting them last is the fix (C2).
- **Partial-success DML** (`Database.upsert(rows, false)`) keeps one bad log row from failing the business transaction.
- **Masking at the source:** mask before storing, not in the report — once a PAN is in a Long Text field, every user with read access can see it (NFR-06).
- **Interfaces + `Type.forName`** let a generic batch call any service without a hardcoded switch.

## Done when

- [ ] 200 logs started, completed and flushed use exactly one DML statement; flush with an empty buffer uses none
- [ ] `mask('PAN ABCDE1234F acct 123456789012')` keeps only the last 4 of each; text without sensitive data is unchanged; null returns null
- [ ] Correlation Ids are unique across 200 rows; Duration_Ms__c is ≥ 0
- [ ] `failure` sets Status Failed and Next_Retry_At__c = now + 1 h; `retried` on the same row increments Retry_Count__c and sets Success, or Retrying with now + 2^n hours (2 h after the first retry, 4 h after the second); no new row is inserted
- [ ] Response longer than the field is truncated, not rejected
- [ ] The fake retryable is created through `Type.forName(...).newInstance()` and its `retry` updates the same log row
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-65, BR-66, §10.9 Integration\_Log\_\_c, §11 OWD Integration\_Log\_\_c, §14 callout rule, IntegrationLogger, IntegrationRetryable, IntegrationRetryBatch, C2, NFR-06
