# LAMS-018 · Integration_Setting__mdt + 5 records

**Milestone:** [M03 – Configuration](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-82

**Depends on:** M02 done; LAMS-006 (mock endpoint paths)

## Goal

Endpoint paths, timeouts, retry limits and fallback mock bodies for the five outbound integrations are custom metadata, so they move between environments with the code and are never typed in by hand (BR-82, NFR-09). On/off and mock mode are not stored here. They live only in LAMS_Settings__c (LAMS-017).

## Build

**Custom metadata type `Integration_Setting__mdt`**: label *Integration Setting*, plural *Integration Settings*. Leave Visibility at its default (Public).

| Field (API name) | Type | Details |
| --- | --- | --- |
| Named_Credential__c | Text(80) | Required. DeveloperName of the Named Credential (LAMS-040) |
| Path__c | Text(255) | Path appended to `callout:<Named_Credential__c>` |
| Timeout_Ms__c | Number(6,0) | Required. Callout timeout, at most 120000 (the platform maximum) |
| Max_Retries__c | Number(2,0) | Required. Retries before the log goes to Gave Up (BR-66) |
| Mock_Response__c | Long Text Area(32768) | Body returned when the integration's mock toggle is on (in-org fallback, see the risk table in the milestones README) |

There is **no `Active__c`** field. The BRD removed it so that each integration has exactly one switch.

**Records** (DeveloperName = the key that services and IntegrationRetryBatch use):

| DeveloperName | Label | Named_Credential__c | Path__c (proposed) | Timeout_Ms__c (proposed) | Max_Retries__c (proposed) |
| --- | --- | --- | --- | --- | --- |
| Credit_Bureau | Credit Bureau | Credit_Bureau | /v1/credit-score | 10000 | 3 |
| KYC | KYC | KYC_Service | /kyc/v1 | 20000 | 3 |
| Payout | Payout | Payout_Service | /v1/payouts | 15000 | 3 |
| SMS | SMS | SMS_Gateway | /v1/messages | 5000 | 2 |
| Core_Banking | Core Banking | Core_Banking | /v1/postings | 10000 | 5 |

Use the paths you actually created on the mock server in LAMS-006. The Named Credential names come from BRD §16.

**Mock_Response__c (proposed bodies):** keep them small and realistic.

| Record | Mock_Response__c |
| --- | --- |
| Credit_Bureau | `{"status":"OK","score":760,"bureauRef":"MOCK-CB-0001"}` |
| KYC | `<kycResponse><status>Verified</status><reference>MOCK-KYC-0001</reference></kycResponse>` |
| Payout | `{"status":"SUCCESS","utr":"MOCKUTR000001"}` |
| SMS | `{"status":"QUEUED","messageId":"MOCK-SMS-0001"}` |
| Core_Banking | `{"status":"POSTED","postingId":"MOCK-CBS-0001"}` |

## Steps

1. Create the type and fields with CLI v2 (or in Setup → Custom Metadata Types):
   ```
   sf cmdt generate object --type-name Integration_Setting --label "Integration Setting" --plural-label "Integration Settings" --output-directory force-app/main/default/objects
   sf cmdt generate field --name Named_Credential --field-type Text --output-directory force-app/main/default/objects/Integration_Setting__mdt
   sf cmdt generate field --name Path --field-type Text --output-directory force-app/main/default/objects/Integration_Setting__mdt
   sf cmdt generate field --name Timeout_Ms --field-type Number --output-directory force-app/main/default/objects/Integration_Setting__mdt
   sf cmdt generate field --name Max_Retries --field-type Number --output-directory force-app/main/default/objects/Integration_Setting__mdt
   sf cmdt generate field --name Mock_Response --field-type LongTextArea --output-directory force-app/main/default/objects/Integration_Setting__mdt
   ```
   Then edit the generated field XML to set the lengths, precision and required flags from the table.
2. Generate the five records, for example:
   `sf cmdt generate record --type-name Integration_Setting --record-name Credit_Bureau --label "Credit Bureau" Named_Credential__c=Credit_Bureau Path__c=/v1/credit-score Timeout_Ms__c=10000 Max_Retries__c=3`
   This writes `force-app/main/default/customMetadata/Integration_Setting.Credit_Bureau.md-meta.xml`. Paste the mock bodies into the XML, escaping `<` and `&` in the KYC body.
3. Deploy: `sf project deploy start --metadata CustomObject:Integration_Setting__mdt CustomMetadata`.
4. Check: `sf data query --query "SELECT DeveloperName, Named_Credential__c, Path__c, Timeout_Ms__c, Max_Retries__c FROM Integration_Setting__mdt"` returns 5 rows.
5. Commit: `feat(config): Integration_Setting__mdt with 5 integration records [LAMS-018]`.

## Learn

- **Custom metadata records are metadata:** they deploy with `sf project deploy start`, are visible in Apex tests without `SeeAllData`, and `Integration_Setting__mdt.getInstance('Credit_Bureau')` doesn't use a SOQL query.
- **Gotcha:** `getInstance()` / `getAll()` return only the first 255 characters of a Long Text Area field. Read `Mock_Response__c` with a SOQL query (`SELECT Mock_Response__c FROM Integration_Setting__mdt WHERE DeveloperName = :name`).
- Apex can't do DML on custom metadata. Changing a record in production means a deploy (or the Metadata API), and that is the point of BR-82.
- Secrets never go here. Credentials belong in External Credentials (LAMS-040), filled in the org by hand.

## Done when

- [ ] `Integration_Setting__mdt` has the 5 fields above and no `Active__c`
- [ ] 5 records exist (Credit_Bureau, KYC, Payout, SMS, Core_Banking) and their Named_Credential__c values match §16
- [ ] Type and records are in `force-app/` (`objects/Integration_Setting__mdt/`, `customMetadata/`) and deploy cleanly
- [ ] An anonymous Apex `System.debug([SELECT Mock_Response__c FROM Integration_Setting__mdt WHERE DeveloperName = 'Credit_Bureau'].Mock_Response__c);` prints the full JSON
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.11 Integration_Setting__mdt, §12 (one switch per integration), §16 Integrations (Named Credential names, mock behaviour), BR-66, BR-69, BR-82, NFR-09
