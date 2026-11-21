# LAMS-058 · PaymentTrigger + PaymentAllocationService (rebuild, advance, payoff, reversal) + tests

**Milestone:** [M08 – Servicing](README.md) · **Size:** L (5–10h) · **Delivers:** BR-42 – BR-46

**Depends on:** LAMS-055 (EmiScheduleService.buildSchedule, used to restore rows), LAMS-056 (Active loans with schedules), LAMS-013 (Payment__c with unique Reference__c, EMI roll-ups), LAMS-032 (Payment__c validation rules), LAMS-036 (LoanEventPublisher)

## Goal

Every successful or reversed payment rebuilds the loan's allocation from scratch: oldest instalment first, late fee then interest then principal, any excess to upcoming rows. A payment that covers the payoff cancels future rows, and the loan closes when every row is Paid or Cancelled (BR-42 – BR-46). This item proves AC-10 (duplicate reference) and AC-12 (reversal) in tests.

## Build

**Trigger `PaymentTrigger`** — `trigger PaymentTrigger on Payment__c (after insert, after update)` → `PaymentTriggerHandler` (proposed). It is the only trigger on Payment__c.

| Event | Rebuild the loan when |
| --- | --- |
| after insert | `Status__c` is Success or Reversed |
| after update | `Status__c` changed (Success → Reversed, Failed → Success) |

The handler collects the `Loan__c` Ids and calls `PaymentAllocationService.rebuild(loanIds)` once. For newly inserted Success payments it also publishes a *Payment Received* event through LoanEventPublisher (BR-68; proposed event type value). A Reversed payment must carry `Reversal_Reason__c`. If LAMS-032 has no such rule, add validation rule `Payment_Reversal_Reason_Required` (proposed).

**Class `PaymentAllocationService`** — `public without sharing class`. It runs for the Integration User and portal context too, and only it may write `Amount_Paid__c` (§10.6).

| Method | Signature |
| --- | --- |
| Rebuild | `public static void rebuild(Set<Id> loanIds)` |
| Invocable | `@InvocableMethod(label='Rebuild Payment Allocation') public static void rebuildForFlow(List<Id> loanIds)` (proposed; used by Waive Late Fee, LAMS-060) |
| Row status | `public static String statusFor(EMI_Instalment__c row, Date today)` (reused by LAMS-059) |
| DPD | `public static Integer daysPastDue(List<EMI_Instalment__c> rows, Date today)` (reused by LAMS-059) |

Per row, with `a` = Amount_Paid__c: fee+interest = Late_Fee__c + Interest_Component__c; unpaid principal = Principal_Component__c − MIN(Principal_Component__c, MAX(0, a − fee+interest)), which is the same rule as the Principal_Paid__c formula.

`rebuild` algorithm for each loan, using 2 queries in total (loans with instalments sub-query ordered by Instalment_No__c; Success payments ordered by Loan__c, Payment_Date__c, CreatedDate, Name):

1. **Reset.** `EmiScheduleService.buildSchedule(loan)` gives the original rows. For each instalment, restore EMI_Amount__c, Interest_Component__c, Principal_Component__c and Closing_Balance__c from the original with the same Instalment_No__c, then set `Amount_Paid__c` = 0 and `Paid_Date__c` = null. Keep Late_Fee__c, Late_Fee_Waived__c and Waiver_Reason__c; the nightly batch and the waiver flow own those.
2. **Replay** each Success payment *p* (date D, amount A) in date order:
   1. Calculate **payoff(D)** = Σ unpaid principal on all rows + Σ unpaid fee+interest on rows with Due_Date__c ≤ D. This matches the quote in LAMS-061.
   2. **If A ≥ payoff(D) > 0 (full payoff, BR-44):**
      - Rows with Due_Date__c ≤ D: Amount_Paid__c = EMI + Late_Fee, Paid_Date__c = D.
      - Rows with Due_Date__c > D: Interest_Component__c = the interest already paid on that row, EMI_Amount__c = Interest + Principal_Component, Amount_Paid__c = EMI_Amount__c, Closing_Balance__c = 0, Status__c = **Cancelled**, Paid_Date__c = D.
      - Any excess (A − payoff), and any later payments, stay unallocated. Create a Task for Assigned_Officer__c, Subject label `LAMS_Task_Refund_Excess` (proposed).
      - Stop replaying.
   3. **Otherwise, pay oldest first (BR-42, BR-43):** remaining = A. Then for each row in Instalment_No__c order: due = EMI + Late_Fee − Amount_Paid; take = MIN(remaining, due); add `take` to Amount_Paid__c; if the row is now fully paid, set Paid_Date__c = D; stop when remaining = 0. Upcoming rows are included, so excess becomes an advance payment. The split inside a row (late fee → interest → principal) follows from the Principal_Paid__c formula.
3. **Row status** (except Cancelled) with `statusFor(row, today)`:

| Condition (in order) | Status__c |
| --- | --- |
| balance (EMI + Late_Fee − Amount_Paid) ≤ 0 | Paid |
| Due_Date__c < today | Overdue |
| Amount_Paid__c > 0 | Partly Paid |
| Due_Date__c = today | Due |
| else | Upcoming |

4. **Loan:** `Days_Past_Due__c = daysPastDue(rows, today)`, the age of the oldest Overdue row or 0, so a payment improves the bucket at once.
   - All rows Paid or Cancelled → `Status__c` = Closed, `Closure_Type__c` = Prepaid if any row is Cancelled, else Matured. When the loan becomes Closed, publish *Loan Closed* (BR-46; the closure letter and email follow in LAMS-065/LAMS-066).
   - The loan was Closed and the rebuild leaves unpaid rows (a reversal) → `Status__c` = Active, Closure_Type__c cleared.
5. **DML:** one update of the changed instalments and one update of the changed loans. The roll-ups (Total_Paid__c, Principal_Repaid__c, Overdue_Amount__c, Next_Due_Date__c) then recalculate on the server.

Loans with no instalments (still Pending Disbursement) are skipped. Payments are never edited (BR-45): corrections are a status change to Reversed, which re-runs the rebuild.

## Steps

1. Write `PaymentAllocationService`, `PaymentTriggerHandler` and `PaymentTrigger`.
2. In `TestDataFactory`, add `createActiveLoanWithSchedule(principal, ratePct, tenure, disbursementDate)` (proposed). It inserts the loan and calls `EmiScheduleService.createSchedules`.
3. Write `PaymentAllocationServiceTest` (AC-09 loan, ₹1,00,000, 14%, 12 months, EMI ₹8,979):
   - one payment of ₹8,979 → row 1 Paid, rows 2–12 Upcoming, Outstanding_Principal__c = ₹92,188
   - ₹5,000 → row 1 Partly Paid with Amount_Paid ₹5,000; Principal_Paid = ₹5,000 − ₹1,167 = ₹3,833
   - row 1 overdue with Late_Fee ₹180, pay ₹9,159 → the fee is paid first, then the row is Paid
   - advance: ₹20,000 → rows 1–2 Paid, row 3 Partly Paid ₹2,042
   - payoff: after 3 EMIs, pay ₹76,289 before row 4's due date → rows 4–12 Cancelled, loan Closed, Closure_Type Prepaid, Outstanding_Principal 0
   - all 12 EMIs paid → Closed, Matured
   - **AC-12:** loan X gets payments ₹8,979 / ₹5,000 / ₹8,979 on three dates, then the 2nd is reversed. Loan Y gets only the 1st and 3rd. Every row's Amount_Paid__c, Status__c and Paid_Date__c must be equal between X and Y
   - reversing the payoff payment reopens the loan (Active) and restores the cancelled rows
   - **AC-10:** inserting two payments with the same Reference__c throws `DUPLICATE_VALUE`; `Database.upsert(p, Payment__c.Reference__c)` twice gives one record and one rebuild
   - bulk: 200 loans × 1 payment in one insert → 200 rows Paid; assert ≤ 4 queries in the service
4. `sf apex run test --class-names PaymentAllocationServiceTest --code-coverage --result-format human --wait 10`
5. Commit: `feat(apex): PaymentAllocationService rebuild with advance, payoff and reversal [LAMS-058]`.

## Learn

- **Rebuild beats incremental.** Undoing one payment's effect is error-prone once late fees, advances and payoffs mix. Resetting and replaying every Success payment in date order always gives the same answer (BR-45, AC-12).
- **Formula fields are stale in memory.** After you set Amount_Paid__c in Apex, `Balance_Due__c` and `Principal_Paid__c` still hold the old values until the record is re-queried. Calculate them in Apex, or call `Formula.recalculateFormulas(rows)`.
- **Roll-up summaries recalculate after the child DML** and fire the parent's triggers. LoanTrigger runs again, so it must be a no-op when nothing it cares about changed.
- **Idempotency with External ID + Unique:** `Reference__c` blocks duplicate inserts at the database, and an upsert on it turns a repeated gateway callback into an update (AC-10, NFR-05).

## Done when

- [ ] AC-10: the same payment reference sent twice results in one Payment__c (test passes; the API part follows in LAMS-070)
- [ ] AC-12: after reversing the second of three payments, every instalment matches a fresh allocation of the remaining two (test passes)
- [ ] Oldest-first, fee → interest → principal, advance, payoff (future rows Cancelled) and closure (Matured / Prepaid) tests all pass
- [ ] Reversing a payoff reopens the loan; Total_Paid__c excludes Reversed payments
- [ ] 200-payment bulk test passes; coverage ≥ 90% for PaymentAllocationService and PaymentTriggerHandler
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.7 BR-41 – BR-47, §9 AC-10, AC-12, §10.5 Loan__c roll-ups, §10.6 EMI_Instalment__c (Principal_Paid__c, Balance_Due__c, Cancelled), §10.7 Payment__c, §13.1 Payment__c rules, §14 PaymentTrigger + PaymentAllocationService, BR-68, NFR-05, Appendix #11
