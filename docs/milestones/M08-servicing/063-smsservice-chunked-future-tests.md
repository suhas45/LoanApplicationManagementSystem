# LAMS-063 · SmsService (chunked @future) + tests

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-53

**Depends on:** LAMS-062 (Send Notification has the SMS placeholder), LAMS-040 (Named Credential `SMS_Gateway`), LAMS-018 (Integration_Setting__mdt `SMS`), LAMS-039 (IntegrationLogger, IntegrationRetryable), LAMS-019 (FeatureToggle: SMS_Enabled__c)

## Goal

When SMS is enabled, every borrower notification also goes by SMS in the borrower's language (BR-53, BR-54). Flow hands the whole list to Apex, which sends up to 100 messages per `@future` call, so 200 notifications use 2 future calls, not 200.

## Build

**Class `SmsService`** — `public with sharing class SmsService implements IntegrationRetryable`.

| Member | Signature |
| --- | --- |
| Request | `public class SmsRequest { @InvocableVariable(required=true) public Id recipientId; @InvocableVariable(required=true) public String templateName; @InvocableVariable public Id recordId; }` |
| Invocable | `@InvocableMethod(label='Send SMS') public static void send(List<SmsRequest> requests)` |
| Future | `@future(callout=true) static void sendChunk(String messagesJson)` |
| Retry | `public void retry(Integration_Log__c log)` re-sends the one message stored in the log (LAMS-039 contract) |
| Constant | `@TestVisible static final Integer CHUNK_SIZE = 100;` |

`send` algorithm:

1. If `SMS_Enabled__c` is off (FeatureToggle), return. Flow checks it too; Apex is the real guard (BR-80).
2. One query loads the Contacts (MobilePhone, Preferred_Language__c). Skip contacts without a mobile number.
3. Record names: group `recordId`s by SObjectType and run one query per type for `Name`. Case uses CaseNumber.
4. Text: `String.format(System.Label.get('', templateName + '_SMS', lang), new List<String>{ recordName })`, with lang = `hi` for Hindi, otherwise `en_US`. Labels (proposed, with Hindi translations), max 160 characters:
   `LAMS_Application_Submitted_SMS`, `LAMS_Document_Rejected_SMS`, `LAMS_Application_Approved_SMS`, `LAMS_Application_Rejected_SMS`, `LAMS_Offer_Expiring_SMS`, `LAMS_Loan_Disbursed_SMS`, `LAMS_EMI_Due_SMS`, `LAMS_EMI_Overdue_SMS`, `LAMS_Loan_Closed_SMS`.
5. Build `List<SmsMessage>` (`phone`, `text`, `recordId`). Split it into chunks of `CHUNK_SIZE`, and for each chunk call `sendChunk(JSON.serialize(chunk))`.
6. **Guard:** if `System.isFuture() || System.isBatch()`, or if `Limits.getFutureCalls()` + chunks > `Limits.getLimitFutureCalls()`, do not call `@future`. Instead, write each message as an Integration_Log__c row with Status Failed and `Next_Retry_At__c` = now. IntegrationRetryBatch (M09) sends it within the hour through `retry()`.

`sendChunk` algorithm:

1. Read `Integration_Setting__mdt` `SMS` (Named_Credential__c, Path__c, Timeout_Ms__c).
2. For each message, `POST callout:SMS_Gateway` + Path__c with `{"to": phone, "text": text, "ref": correlationId}` and the timeout. Success = HTTP 2xx. A `CalloutException` or other status counts as Failed, with `Next_Retry_At__c` set.
3. Buffer one IntegrationLogger row per message (Integration__c = SMS, Outbound, Related_Record_Id__c, Correlation_Id__c, HTTP_Status__c, Duration_Ms__c, Request__c). Flush once after all callouts.

**Wire into `Send_Notification`** (LAMS-062): on the "SMS on" path of the `{!$Setup.LAMS_Settings__c.SMS_Enabled__c}` decision, add the Apex action *Send SMS* with recipientId, templateName and recordId. When 200 interviews reach the action in one transaction, Flow passes all 200 requests to one `send` call.

## Steps

1. Add the 9 `_SMS` labels and their Hindi translations.
2. Write `SmsService` and `SmsMock implements HttpCalloutMock` (proposed; returns 200 or 500 by flag).
3. Add the *Send SMS* action to Send Notification. Activate the new flow version.
4. Write `SmsServiceTest`:
   - toggle on, 200 requests inside `Test.startTest()`: `Limits.getFutureCalls()` = 2 right after `send`. After `Test.stopTest()` there are 200 Integration_Log__c rows with Integration SMS and Status Success
   - toggle off → 0 future calls, 0 log rows
   - mock 500 → rows Failed with Next_Retry_At__c set
   - Hindi contact → text equals `System.Label.get('', 'LAMS_Loan_Disbursed_SMS', 'hi')` formatted; English contact gets en_US
   - contact without MobilePhone → skipped, no log
   - `retry(log)` re-sends one message and updates the log
   - async-context guard: call `send` from the `execute` of a small test batch class → no future call, Failed log rows ready for retry
5. `sf apex run test --class-names SmsServiceTest --code-coverage --result-format human --wait 10`
6. Demo: switch SMS on in lamsSettings, disburse a loan, and check the Integration Log and the mock's request history.
7. Commit: `feat(integration): SmsService chunked @future sender [LAMS-063]`.

## Learn

- **@future limits:** 50 future calls per transaction, and each future call has its own limit of 100 callouts. One call per record breaks at the 51st record. Chunking by 100 matches the callout limit and uses the fewest calls (BRD appendix #14).
- **@future takes only primitives** (and collections of them), so pass the chunk as a JSON string, not as objects or sObjects.
- **@future cannot be called from batch or another future.** Check `System.isBatch()`/`System.isFuture()` and fall back to the retry queue instead of throwing.
- Each future transaction has 120 seconds of total callout time. Keep Timeout_Ms__c low (for example 5,000), because 100 slow calls would exceed it.

## Done when

- [ ] A 200-request test uses exactly 2 future calls and writes 200 log rows
- [ ] With SMS_Enabled__c off, no SMS is attempted; on, the same events as email are also sent by SMS
- [ ] Hindi borrowers get the Hindi text from the translated label
- [ ] Failures are logged with Next_Retry_At__c; calls from batch/future context are queued for retry rather than failing
- [ ] `SmsServiceTest` passes with HttpCalloutMock; coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.9 BR-53, BR-54, §8 C2 (50 future calls, 100 callouts), §10.9 Integration_Log__c, §10.11 Integration_Setting__mdt, §12 SMS_Enabled__c, §13.2 Send Notification, §14 SmsService, §16 SMS Gateway, BR-65, BR-66, Appendix #14
