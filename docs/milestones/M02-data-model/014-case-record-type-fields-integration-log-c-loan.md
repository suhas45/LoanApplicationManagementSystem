# LAMS-014 · Case record type + fields, Integration_Log__c, Loan_Event__e, CDC

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** §10.8 – §10.10

**Depends on:** LAMS-012, LAMS-013 (Loan__c and Payment__c, for the Case lookup and CDC); LAMS-009 (Loan_Application__c)

## Goal

The remaining data structures exist: service requests as Cases (BR-57, BR-58), a log row for every external call (BR-65, BR-66), a platform event for business events (BR-68), and Change Data Capture on loans and payments for core banking and subscribers (BR-47). This completes every object in §10 except the settings, which are M03.

## Build

**Case**

| Item | Value |
| --- | --- |
| Support process | `LAMS Service Process` (proposed), from the *Master* process; statuses New, Working, Escalated, Closed |
| Record type | DeveloperName `Loan_Service_Request`, label *Loan Service Request*, support process above; make it the default for System Administrator |
| Origin (standard value set `CaseOrigin`) | Add Portal and Agent (Phone exists). The record type shows only Portal, Agent, Phone |

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan__c | Lookup(Loan__c) | Child relationship `Cases`; delete behaviour *Clear the value* |
| Loan_Application__c | Lookup(Loan_Application__c) | Child relationship `Cases`; *Clear the value* |
| Request_Type__c | Picklist (restricted) | Statement, Prepayment Quote, Address Change, Dispute. Required on the layout (LAMS-015), not at field level (proposed), so other Case sources are not broken |
| Prepayment_Quote_Amount__c | Currency(16,2) | Written by the Prepayment Quote flow (LAMS-061, BR-44) |

**Object `Integration_Log__c`** — label *Integration Log*; Name = Auto Number `IL-{0000000}` (proposed); enable Reports (BR-64 dashboard) and Activities (Gave Up tasks).

| Field (API name) | Type | Details |
| --- | --- | --- |
| Integration__c | Picklist (restricted) | Labels: Credit Bureau, KYC, Payout, SMS, Core Banking, Partner API, Payment Callback, Loan Status SOAP. API names (proposed): `Credit_Bureau`, `KYC`, `Payout`, `SMS`, `Core_Banking`, `Partner_API`, `Payment_Callback`, `Loan_Status_SOAP`, so the first five equal the Integration_Setting__mdt record names (LAMS-018) |
| Direction__c | Picklist (restricted) | Inbound, Outbound (proposed values) |
| Related_Record_Id__c | Text(18) | Application, loan or payment Id |
| Correlation_Id__c | Text(36) | Required, Unique (case-insensitive), External ID. A UUID |
| Status__c | Picklist (restricted) | Success, Failed, Retrying, Gave Up |
| HTTP_Status__c | Number(3,0) | |
| Request__c | Long Text Area(131072) | Masked by IntegrationLogger (LAMS-039) |
| Response__c | Long Text Area(131072) | Masked |
| Duration_Ms__c | Number(8,0) | |
| Retry_Count__c | Number(2,0) | Default 0 |
| Next_Retry_At__c | Date/Time | Read by IntegrationRetryBatch (LAMS-072) |

**Platform event `Loan_Event__e`** — label *Loan Event*; Event Type *High Volume*; Publish Behavior **Publish After Commit**.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Event_Type__c | Text(40) | Required. Values (proposed, from BR-68 and §13.2): Application Submitted, Application Approved, Application Rejected, Loan Disbursed, Payment Received, Loan Overdue, Loan Closed |
| Record_Id__c | Text(18) | |
| Loan_Number__c | Text(20) | |
| Amount__c | Number(16,2) | Platform events have no Currency type |
| Payload__c | Long Text Area(131072) | JSON |

**Change Data Capture** — Setup → Change Data Capture → Selected Entities: *Loan (Loan__c)* and *Payment (Payment__c)*. Record how many of the org's entity slots this uses in [ORG_NOTES.md](../M01-org-and-repo/ORG_NOTES.md).

**Also:** a tab for Integration_Log__c; a list view *Failed and Retrying* (Status__c in Failed, Retrying) showing Integration, Status, HTTP Status, Retry Count, Next Retry At, Created Date.

## Steps

1. Create the support process, then the Case record type; add Portal and Agent to Case Origin; set the record type's Origin values.
2. Create the four Case fields.
3. Create `Integration_Log__c`, its fields, tab and list view.
4. Create `Loan_Event__e` and its fields.
5. Select Loan__c and Payment__c in Change Data Capture.
6. Retrieve:
   `sf project retrieve start --metadata RecordType:Case.Loan_Service_Request BusinessProcess CustomField:Case.Loan__c CustomField:Case.Loan_Application__c CustomField:Case.Request_Type__c CustomField:Case.Prepayment_Quote_Amount__c StandardValueSet:CaseOrigin CustomObject:Integration_Log__c CustomTab:Integration_Log__c CustomObject:Loan_Event__e PlatformEventChannelMember`
7. Smoke test the event in Developer Console → Execute Anonymous:
   ```apex
   Database.SaveResult r = EventBus.publish(new Loan_Event__e(Event_Type__c = 'Test', Record_Id__c = '001000000000000'));
   System.debug(r.isSuccess());
   ```
8. Commit: `feat(data-model): Case service request, Integration_Log__c, Loan_Event__e and CDC [LAMS-014]`.

## Learn

- **Case record types need a support process**, which decides the Status values available, just as sales processes do for Opportunity.
- **Standard picklists** (Case Origin) are standard value sets: values are org-wide; record types only choose which ones show.
- **Publish After Commit** means a rolled-back transaction never sends the event, so subscribers never hear about work that did not happen; *Publish Immediately* would.
- **CDC vs platform events:** CDC publishes every field change automatically (`Loan__ChangeEvent`, `Payment__ChangeEvent`); a platform event carries only what your code chooses to say. Developer Edition allows only a few CDC entities.

## Done when

- [ ] A Case with record type *Loan Service Request*, Request Type *Dispute*, Origin *Portal* and a Loan saves, and appears on the loan's Cases related list
- [ ] An Integration_Log__c row saves; a second row with the same Correlation_Id__c fails
- [ ] The anonymous Apex publish prints `true`
- [ ] Setup → Change Data Capture lists Loan and Payment under Selected Entities
- [ ] All of the above is in source and `sf project deploy start --dry-run --source-dir force-app` succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.5 (CDC note), §10.8 Case, §10.9 Integration_Log__c, §10.10 Loan_Event__e, §10.11; §16 Integrations; §19 checklist (CDC); BR-44, BR-47, BR-57, BR-58, BR-64 – BR-66, BR-68
