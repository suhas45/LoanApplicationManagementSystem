# LAMS-042 · KycService (WSDL2Apex) + WebServiceMock tests

**Milestone:** [M06 – Origination](README.md) · **Size:** L (5–10h) · **Delivers:** BR-10, BR-13

**Depends on:** LAMS-039 (IntegrationLogger, IntegrationRetryable), LAMS-040 (KYC_Service credential), LAMS-041 (chains this job), LAMS-043 (EligibilityService, called at the end), LAMS-006 (KYC SOAP mock), LAMS-018 (KYC metadata record)

## Goal

KYC is verified through the provider's SOAP service, or reused if it was verified within KYC_Reuse_Months__c (BR-10), and the result is stored on the borrower. The job then runs eligibility, which now always sees both the score and the KYC result (§14); KYC Rejected makes the result Fail (BR-13). Completes **AC-04**.

## Build

**WSDL** (D3) — write a small document/literal WSDL and keep it in the repo at `docs/integrations/kyc/KycService.wsdl` (proposed; outside `force-app`, so it is not deployed). WSDL2Apex accepts one file with no imports.

| WSDL part | Value (proposed; match the LAMS-006 mock) |
| --- | --- |
| Service / port | `KycVerificationService` / `KycVerificationPort` |
| Operation | `verifyKyc` |
| Request | `pan`, `fullName`, `dateOfBirth` (xsd:date), `correlationId` |
| Response | `status` (`VERIFIED` \| `REJECTED` \| `PENDING`), `referenceId`, `reason` |

**Generated class** — Setup → Apex Classes → **Generate from WSDL** → upload the file → Apex class name `KycSoapClient` (proposed). Commit the generated `KycSoapClient.cls` (and `AsyncKycSoapClient.cls` if generated; unused). Do not hand-edit it; regenerate instead.

**Class `KycService`** — `public without sharing class KycService implements Queueable, Database.AllowsCallouts, IntegrationRetryable` (runs as the submitter, may be a portal borrower; it writes Contact KYC fields).

```apex
public KycService();                          // no-arg: IntegrationRetryBatch creates it by name
public KycService(Set<Id> applicationIds);
public void execute(QueueableContext ctx);
public void retry(Integration_Log__c failedLog);   // IntegrationRetryable
```

**`execute` — callouts first, then DML**

| Phase | Work |
| --- | --- |
| 1 Read | Settings by SOQL `... FROM Integration_Setting__mdt WHERE DeveloperName = 'KYC'` (`getInstance()` truncates Mock_Response__c); applications with Borrower__c, Borrower__r PAN__c, Name, Birthdate, KYC_Status__c, KYC_Verified_Date__c |
| 2 Reuse | Skip a borrower when KYC_Status__c = Verified **and** KYC_Verified_Date__c ≥ `Date.today().addMonths(-KYC_Reuse_Months__c)` (FeatureToggle, default 12). Call each remaining borrower **once**, even with several applications in the job |
| 3 Call | `IntegrationLogger.start('KYC','Outbound', app.Id)`. `FeatureToggle.isMockMode('KYC')` (KYC_Mock_Mode__c) on → no callout, status from Mock_Response__c (e.g. `VERIFIED`). Off → `KycSoapClient.KycVerificationPort port = new KycSoapClient.KycVerificationPort(); port.endpoint_x = 'callout:KYC_Service' + Path__c; port.timeout_x = Timeout_Ms__c;` then `port.verifyKyc(...)` |
| 4 Map | VERIFIED → KYC_Status__c Verified, KYC_Verified_Date__c = today; REJECTED → Rejected; PENDING or any failure → unchanged (Pending) and `IntegrationLogger.failure(...)` |
| 5 DML | One update of the Contacts |
| 6 Log | `IntegrationLogger.flush()` |
| 7 Eligibility | `EligibilityService.evaluate(applicationIds)` — it skips applications still without a score |
| 8 Route | `ApplicationRouter` call added here in LAMS-046 |

The SOAP stub does not expose the raw XML, so Request__c / Response__c hold a masked summary (`pan=XXXXXX234F status=VERIFIED ref=…`).

**Mock conventions (LAMS-006):** the 9th character of the PAN (its last digit) drives the SOAP mock — `7` → `REJECTED`; `6` → SOAP fault; any other → `VERIFIED`. Seed borrowers in LAMS-016 use these.

**`retry(failedLog)`** (IntegrationRetryable contract, LAMS-039) — rebuilds the request from `failedLog.Related_Record_Id__c` (the application; Request__c is masked), re-verifies its borrower, records the attempt on the **same** log row with `IntegrationLogger.retried(...)` (Success, or Retrying with 2^n-hour backoff), updates the Contact, flushes, then re-runs eligibility for that application. IntegrationRetryBatch marks Gave Up and raises the owner Task (BR-66); KYC then stays Pending, which only blocks auto-approve (BR-27).

**Tests `KycServiceTest`** with `KycWebServiceMock implements WebServiceMock` (`@IsTest`):

```apex
public void doInvoke(Object stub, Object request, Map<String, Object> response,
    String endpoint, String soapAction, String requestName,
    String responseNS, String responseName, String responseType) {
    KycSoapClient.verifyKycResponse_element res = new KycSoapClient.verifyKycResponse_element();
    res.status = statusToReturn;  // configurable; or throw new CalloutException()
    response.put('response_x', res);
    calls++;                      // static counter to assert how many callouts ran
}
```

(The exact element class name comes from your generated `KycSoapClient`.)

## Steps

1. Write `docs/integrations/kyc/KycService.wsdl`; make the LAMS-006 mock return a matching SOAP envelope.
2. Setup → Apex Classes → Generate from WSDL → parse → class name `KycSoapClient` → Generate. Retrieve: `sf project retrieve start --metadata ApexClass:KycSoapClient`.
3. Replace the LAMS-041 stub: `sf apex generate class --name KycService --output-dir force-app/main/default/classes` (overwrite), plus `KycWebServiceMock` and `KycServiceTest`.
4. Write an end-to-end test `OriginationChainTest` for AC-04 (below).
5. `sf project deploy start --source-dir force-app/main/default/classes`
6. `sf apex run test --class-names KycServiceTest OriginationChainTest --code-coverage --result-format human --wait 10`
7. Manual AC-04: Bureau mock mode off, Beeceptor rule delays the bureau response 30 s (Timeout_Ms__c for Credit_Bureau must be above 30,000, e.g. 60,000); submit; refresh during the wait — no Eligibility_Run_Date__c; after the score arrives, eligibility appears (NFR-03: within 2 minutes).
8. Commit: `feat(apex): KycService via WSDL2Apex with reuse and WebServiceMock [LAMS-042]`.

## Learn

- **WSDL2Apex** turns a WSDL into typed stub classes; `endpoint_x` and `timeout_x` on the port are how you point it at a Named Credential and set the timeout.
- **WebServiceMock vs HttpCalloutMock:** SOAP stubs call `WebServiceCallout.invoke`, which only `WebServiceMock` intercepts; you fill `response_x` with the generated response element.
- **Dedupe before calling out:** two applications for one borrower must not cost two callouts — callouts are limited (100 per transaction) and slow.
- **Why the chain order matters:** callouts (KYC) → DML (Contact) → eligibility DML is legal; eligibility before the KYC callout would be "callout after uncommitted work".

## Done when

- [ ] VERIFIED → Contact Verified with today's KYC_Verified_Date__c; REJECTED (PAN last digit 7) → Rejected and the application's eligibility is Fail (BR-13)
- [ ] KYC verified 3 months ago → no callout (mock counter 0); 13 months ago → callout made
- [ ] Two applications for one borrower in a job → one callout
- [ ] SOAP fault (PAN last digit 6) / `CalloutException` → KYC stays Pending, Failed log, eligibility still runs, no exception escapes
- [ ] `retry` updates the same log row (Success or Retrying, Retry_Count__c + 1); the class has a public no-arg constructor
- [ ] Mock mode on → no callout, status from Mock_Response__c (read by SOQL)
- [ ] Every call logged with masked PAN and correlation Id
- [ ] **AC-04** (`OriginationChainTest`): submit inside `Test.startTest()`; before `stopTest()` Credit_Score__c and Eligibility_Run_Date__c are blank; after `stopTest()` (bureau job ran) the score is saved; running `new KycService(ids).execute(null)` with the mock then sets Eligibility_Run_Date__c and a result; an application whose bureau call failed still has no Eligibility_Run_Date__c after KYC
- [ ] Bulk: a 50-application job with 50 borrowers runs within limits (50 callouts, 1 Contact DML, 1 log DML); 200 submissions flow through 4 bureau jobs
- [ ] Coverage ≥ 90% (generated `KycSoapClient` is covered by the mock calls)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-10, BR-11, BR-13, BR-65, BR-69, §10.1 KYC fields, §12 KYC\_Mock\_Mode\_\_c, KYC\_Reuse\_Months\_\_c, §14 corrected origination chain, callout rule, KycService, §16 KYC Provider, D3, NFR-03, AC-04
