# LAMS-070 · PaymentCallbackApi + tests

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** M (2–5h) · **Delivers:** BR-41

**Depends on:** LAMS-068 (Integration User, token), LAMS-013 (Payment__c with unique `Reference__c`), LAMS-032 (Payment__c lock rules), LAMS-058 (PaymentTrigger + PaymentAllocationService), LAMS-039 (IntegrationLogger)

## Goal

The payment gateway posts each payment to LAMS; the same reference sent twice creates only one payment (BR-41, AC-10, NFR-05), and a new payment is allocated by the existing PaymentTrigger.

## Build

**Class** `global with sharing class PaymentCallbackApi` with `@RestResource(urlMapping='/lams/v1/payments/*')` (same pattern as LoanApplicationApi, LAMS-069)

| Method | Signature | URL |
| --- | --- | --- |
| POST | `@HttpPost global static void receivePayment()` | `/services/apexrest/lams/v1/payments` |

**Request**

```json
{"reference": "PG-20261121-000045", "loanNumber": "LN-000045", "amount": 8979,
 "paymentDate": "2026-11-21", "mode": "Online", "status": "Success"}
```

| JSON | Field | Rule |
| --- | --- | --- |
| reference | `Reference__c` | Required; unique key |
| loanNumber | `Loan__c` (by Loan Name `LN-…`) | Not found → 404 |
| amount | `Amount__c` | > 0 |
| paymentDate | `Payment_Date__c` | ISO date |
| mode | `Mode__c` | Online, Auto-Debit, Bank Transfer, Cash |
| status | `Status__c` | Success, Failed, Reversed |
| reversalReason | `Reversal_Reason__c` | Required when status = Reversed |

**Behaviour and status codes** (payments are never edited, BR-45, so "upsert" here means *insert once, then only status may move*):

| Case | Code | Body / effect |
| --- | --- | --- |
| New reference | **201** | `{"reference":"PG-…","paymentId":"a05…","status":"Success","duplicate":false}`; PaymentTrigger allocates |
| Same reference, same loan and amount, same status | **200** | `{"duplicate":true,…}`; no DML (AC-10) |
| Same reference, status Success → Reversed (with reason) | **200** | Only `Status__c` and `Reversal_Reason__c` updated; allocation re-runs (BR-45) |
| Same reference, different loan or amount | **409** | `{"errorCode":"REFERENCE_CONFLICT"}`; nothing changed |
| Unknown loan number | **404** | `{"errorCode":"LOAN_NOT_FOUND"}` |
| Loan not Active (proposed rule) | **400** | `{"errorCode":"LOAN_NOT_ACTIVE"}` |
| Bad JSON, amount ≤ 0, bad mode, missing reason | **400** | `{"errorCode":"INVALID_REQUEST","message":…}` |
| Unexpected exception | **500** | Generic message; detail in the log |

There is no toggle for this endpoint (§16 shows "–").

**Race guard:** if the insert fails with `DUPLICATE_VALUE` on `Reference__c` (two callbacks at once), re-query and answer as the duplicate case (200).

**Access:** the Integration User finds any loan through View All (read) on `Loan__c`, and the Payment__c master-detail sharing is Read Only, so read on the loan is enough to create the payment (§11).

**Logging:** Integration__c `Payment Callback`, Direction__c `Inbound`, Correlation_Id__c from `X-Correlation-Id` or a new UUID, HTTP_Status__c = the code returned.

**Test class `PaymentCallbackApiTest`:** `RestContext.request` / `RestContext.response` as in LAMS-069; an Active loan with a 12-row schedule from the TestDataFactory.

## Steps

1. Write `PaymentCallbackApi` (parse → find loan → find existing payment → insert / update status / reject → log → respond).
2. Add it to `LAMS_Integration` Apex Class Access.
3. Write `PaymentCallbackApiTest`:
   - New reference → 201, one payment, instalment 1 `Amount_Paid__c` = 8,979.
   - **AC-10:** the same body twice → second call 200 `duplicate:true`, `SELECT COUNT() FROM Payment__c WHERE Reference__c = …` = 1, instalment amounts unchanged.
   - Reversal → 200, status Reversed, allocation rebuilt (balances as if the payment never happened).
   - Same reference, different amount → 409; unknown loan → 404; amount 0 → 400; Reversed with no reason → 400.
   - A simulated `DUPLICATE_VALUE` race (insert the payment directly, then call) → 200.
   - Every call → one Payment Callback log row.
   - Bulk: a single-payment endpoint; note it in the class header (allocation bulk is tested in LAMS-058).
4. Run `sf apex run test --class-names PaymentCallbackApiTest --code-coverage --result-format human`.
5. In Postman: POST a payment for a demo loan, then the exact same request again; confirm one payment in the org.
6. Commit: `feat(api): PaymentCallbackApi idempotent gateway callback [LAMS-070]`.

## Learn

- **Callbacks are retried by gateways**, often several times; an idempotency key plus a unique index is the only reliable defence.
- **Why not a blind `upsert`:** `Database.upsert` on `Reference__c` would try to update Amount and Loan on a resend, which the lock rule rejects and BR-45 forbids. Decide per case instead.
- `@HttpPost` with a `void` return lets you send 200 vs 201 vs 409 yourself; returning an object always gives 200.
- The insert fires PaymentTrigger (allocation) and a `Payment__ChangeEvent` (core banking, LAMS-067) in the same request, so keep the API itself thin.

## Done when

- [ ] AC-10: the same payment reference sent twice by Postman leaves exactly one Payment__c and one allocation
- [ ] A new payment returns 201 and is allocated; a reversal returns 200 and re-runs allocation
- [ ] Conflicting resend returns 409; unknown loan 404; invalid body 400
- [ ] Every call writes a Payment Callback log row
- [ ] `PaymentCallbackApiTest` passes with ≥ 90% coverage using `RestContext`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §14 PaymentCallbackApi and PaymentTrigger, §16 Payment Gateway row, §10.7 Payment__c, §11 `LAMS_Integration` and Payment__c sharing, §13.1 Payment__c rules, BR-41, BR-45, BR-65, NFR-05, AC-10
