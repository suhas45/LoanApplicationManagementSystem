# LAMS-036 · LoanEventPublisher + tests

**Milestone:** [M06 – Origination](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-68

**Depends on:** LAMS-014 (Loan_Event__e, publish after commit), LAMS-019 (FeatureToggle)

## Goal

One utility publishes every business event (submitted, approved, rejected, disbursed, payment received, overdue, closed) as a Loan_Event__e for any subscriber, and does nothing when Event_Publishing_Enabled__c is off (BR-68, BR-79, BR-80).

## Build

**Class `LoanEventPublisher`** — `public with sharing class`

```apex
public static final String APPLICATION_SUBMITTED = 'Application Submitted';
public static final String APPLICATION_APPROVED  = 'Application Approved';
public static final String APPLICATION_REJECTED  = 'Application Rejected';
public static final String LOAN_DISBURSED        = 'Loan Disbursed';
public static final String PAYMENT_RECEIVED      = 'Payment Received';
public static final String LOAN_OVERDUE          = 'Loan Overdue';
public static final String LOAN_CLOSED           = 'Loan Closed';

public static Loan_Event__e build(String eventType, Id recordId, String loanNumber,
                                  Decimal amount, Map<String, Object> payload);
public static List<Database.SaveResult> publish(List<Loan_Event__e> events);

@InvocableMethod(label='Publish Loan Event' category='LAMS')
public static void publishFromFlow(List<Request> requests);
```

| Invocable input (`Request`) | Type | Maps to |
| --- | --- | --- |
| `eventType` (required) | String | Event_Type__c — one of the constants |
| `recordId` (required) | Id | Record_Id__c |
| `loanNumber` | String | Loan_Number__c (blank for application events) |
| `amount` | Decimal | Amount__c |
| `payloadJson` | String | Payload__c (already JSON) |

**Behaviour**

- `publish()` first checks `Event_Publishing_Enabled__c` through FeatureToggle (org default via `getOrgDefaults()`, LAMS-019; never read LAMS_Settings__c directly). Off → returns an empty list, publishes nothing.
- One `EventBus.publish(events)` call for the whole list (bulk-safe; Flow passes all interviews' requests in one call).
- Event types use the constants (proposed values; the names Loan Disbursed, Loan Overdue and Loan Closed are the ones §13.2 and §14 already use). An unknown type throws `IllegalArgumentException`.
- Failed `SaveResult`s are written to `System.debug(LoggingLevel.ERROR, …)` and returned to the caller; publishing never throws for a delivery error (the business save must not fail because an event did, NFR-04).
- `@TestVisible private static List<Loan_Event__e> published` collects what was sent, so tests can assert content.

Loan_Event__e must be set to **Publish After Commit** (LAMS-014): if the transaction rolls back, no event goes out.

## Steps

1. `sf apex generate class --name LoanEventPublisher --output-dir force-app/main/default/classes` and `LoanEventPublisherTest`.
2. Write the class and tests.
3. `sf project deploy start --source-dir force-app/main/default/classes`
4. `sf apex run test --class-names LoanEventPublisherTest --code-coverage --result-format human --wait 10`
5. Commit: `feat(apex): LoanEventPublisher with toggle [LAMS-036]`.

## Learn

- **Publish After Commit vs Publish Immediately:** after-commit events follow the transaction (no event for rolled-back work); immediate events go out even on rollback — right for error logging, wrong for business events.
- **Testing platform events:** events published in a test are delivered at `Test.stopTest()` or `Test.getEventBus().deliver()`; you cannot query `Loan_Event__e`, so assert the SaveResults or a test-visible list.
- `EventBus.publish` counts against the DML-statement limit (one call = one statement) — publish the list, never in a loop.

## Done when

- [ ] Toggle on: publishing 200 events in one call returns 200 successful SaveResults and uses one DML statement (`Limits.getDmlStatements()`)
- [ ] Toggle off: nothing published, empty result, no exception
- [ ] Invocable maps every input to the right field; unknown event type throws
- [ ] `build()` serialises the payload map to valid JSON in Payload__c
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-68, BR-79, BR-80, §10.10 Loan\_Event\_\_e, §12 Event\_Publishing\_Enabled\_\_c, §14 LoanEventPublisher, §16 event stream, NFR-04
