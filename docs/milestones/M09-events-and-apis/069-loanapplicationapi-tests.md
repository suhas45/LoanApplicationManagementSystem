# LAMS-069 · LoanApplicationApi + tests

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** M (2–5h) · **Delivers:** BR-06

**Depends on:** LAMS-068 (Integration User, token), LAMS-009 (Loan_Application__c, `External_Reference__c`, record types), LAMS-008 (Contact `PAN__c`), LAMS-019 (FeatureToggle), LAMS-031 (validation rules), LAMS-038 (Application Submitted flow, owner reassignment), LAMS-039 (IntegrationLogger)

## Goal

Dealer and DSA partners create and resubmit applications over REST without ever creating a duplicate, and query status by their own reference (BR-01, BR-06, NFR-05). The API is off unless `Partner_API_Enabled__c` is on (BR-79).

## Build

**Class** `global with sharing class LoanApplicationApi` with `@RestResource(urlMapping='/lams/v1/applications/*')`

| Method | Signature | URL |
| --- | --- | --- |
| POST | `@HttpPost global static void upsertApplication()` | `/services/apexrest/lams/v1/applications` |
| GET | `@HttpGet global static void getStatus()` | `/services/apexrest/lams/v1/applications/{partnerReference}` |

Both read `RestContext.request` and write `RestContext.response` (status code, JSON body, header `X-Correlation-Id`) themselves; `void` methods give full control of the status code.

**POST request** (`Content-Type: application/json`)

```json
{
  "partnerReference": "DSA1-000123",
  "partnerName": "Sharma Motors",
  "productCode": "AL",
  "amount": 600000,
  "tenureMonths": 48,
  "purpose": "New car",
  "submit": false,
  "borrower": {"pan": "ABCDE1234F", "firstName": "Ravi", "lastName": "Kumar", "birthdate": "1990-04-12",
               "email": "ravi@example.com", "mobile": "+919800000000", "employmentType": "Salaried",
               "monthlyIncome": 80000, "existingEmi": 5000, "preferredLanguage": "Hindi"},
  "details": {"vehiclePrice": 750000, "dealerName": "Sharma Motors"}
}
```

| JSON | Field | Rule |
| --- | --- | --- |
| partnerReference | `External_Reference__c` | Required; idempotency key |
| partnerName | `Partner_Name__c` | Required |
| productCode | `Loan_Product__c` (by `Product_Code__c`, Active) | Unknown → 400 |
| amount, tenureMonths, purpose | `Amount__c`, `Tenure__c`, `Purpose__c` | Limits enforced by LAMS-031 rules (BR-03) |
| borrower.* | Contact upserted on `PAN__c` (+ one Account per new borrower) | PAN format `[A-Z]{5}[0-9]{4}[A-Z]` |
| details.propertyValue / vehiclePrice / dealerName / gstNumber / annualTurnover | Product-specific fields (BR-05) | Per record type |
| submit (proposed) | `Status__c` = Submitted when true, else Draft | Submission starts LAMS-038 |
| – | `Channel__c` = Partner API; RecordTypeId from `Loan_Product__c.Record_Type_Name__c` | Set by the API |

**Status codes**

| Case | Code | Body |
| --- | --- | --- |
| New reference | **201** | `{"partnerReference":"DSA1-000123","applicationNumber":"LA-000123","applicationId":"a01…","status":"Draft"}` |
| Existing reference, still Draft | **200** | Same shape; record updated (resend is safe) |
| Existing reference, past Draft | **409** | `{"errorCode":"APPLICATION_LOCKED","status":"Document Review"}`; nothing changed (BR-08) |
| Bad JSON, missing field, unknown product, validation rule error | **400** | `{"errorCode":"INVALID_REQUEST","message":"<validation message>"}` |
| GET unknown reference | **404** | `{"errorCode":"NOT_FOUND"}` |
| `Partner_API_Enabled__c` off (POST and GET) | **503** | `{"errorCode":"PARTNER_API_DISABLED"}`; no DML except the log |
| Unexpected exception | **500** | Generic message; full error in the log only |

**GET response 200:** `{"partnerReference","applicationNumber","status","submittedDate","decisionDate","approvedAmount","offerExpiryDate"}` — never PAN, income, score or eligibility notes.

**Idempotency:** query by `External_Reference__c` first to choose 201/200/409; insert with the key set; if the insert fails with `DUPLICATE_VALUE` (two simultaneous resends), re-query and return 200.

**Sharing (proposed):** the borrower lookup by PAN and the reference lookup run in a small `without sharing` inner class, because a borrower or application may already be owned by someone else after reassignment (LAMS-037); everything else stays `with sharing`.

**Logging:** one `Integration_Log__c` per call: Integration__c `Partner API`, Direction__c `Inbound`, Correlation_Id__c = incoming `X-Correlation-Id` or a new UUID, HTTP_Status__c = the code returned, PAN masked in `Request__c` (BR-65).

**Test class `LoanApplicationApiTest`:** builds `RestContext.request = new RestRequest()` (`requestURI`, `httpMethod`, `requestBody = Blob.valueOf(json)`) and `RestContext.response = new RestResponse()`, calls the method and asserts `statusCode` and the parsed body.

## Steps

1. Write `LoanApplicationApi` with small private helpers: `parse`, `findByReference`, `upsertBorrower`, `respond(Integer code, Object body)`.
2. Add the class to `LAMS_Integration` Apex Class Access (LAMS-068).
3. Write `LoanApplicationApiTest`, with org-default `LAMS_Settings__c` inserted in `@TestSetup`:
   - 201 new; same body again → 200 and still **one** application (BR-06).
   - Resend after Status = Document Review → 409, amount unchanged.
   - `submit: true` → Status Submitted, Channel Partner API.
   - Toggle off → 503 and no application.
   - Unknown product, amount above product max, malformed JSON → 400.
   - GET known → 200 without PAN; GET unknown → 404.
   - Existing borrower PAN → reuses the Contact, no duplicate.
   - Every call → one log row with masked PAN.
   - Bulk: not applicable to a one-record endpoint; state this in the class header comment.
4. Deploy and test: `sf apex run test --class-names LoanApplicationApiTest --code-coverage --result-format human`
5. In Postman (token from LAMS-068): POST twice with the same `partnerReference`, then GET.
6. Commit: `feat(api): LoanApplicationApi partner REST endpoint [LAMS-069]`.

## Learn

- **Apex REST:** `@RestResource(urlMapping=…)` on a `global` class exposes it under `/services/apexrest/`; `@HttpPost`/`@HttpGet` methods must be `global static`. `RestContext` holds the request and response.
- **Idempotency with an External ID:** a unique external key turns "send again" into "update", and the unique index is the last guard against races.
- Inbound Apex runs as the token's user; `with sharing` applies that user's sharing, so plan for what the Integration User can and cannot see.
- Status codes are part of the contract: 409 for "valid request, wrong state", 503 for "switched off on purpose".

## Done when

- [ ] POST with a new reference returns 201; the same request again returns 200 and only one application exists (BR-06, NFR-05)
- [ ] POST for an application past Draft returns 409 and changes nothing
- [ ] With `Partner_API_Enabled__c` off, POST and GET return 503
- [ ] GET by reference returns status with no PAN, income or score
- [ ] Every call writes a Partner API log row with masked PAN
- [ ] `LoanApplicationApiTest` passes with ≥ 90% coverage using `RestContext`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §14 LoanApplicationApi, §16 Dealer/DSA row, §10.3 External_Reference__c and Channel__c, §11 `LAMS_Integration`, §12 Partner_API_Enabled__c, BR-01, BR-03, BR-05, BR-06, BR-07, BR-08, BR-65, NFR-05
