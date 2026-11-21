# LAMS-055 · EmiScheduleService + tests (AC-09)

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-37, BR-39

**Depends on:** LAMS-013 (EMI_Instalment__c fields), LAMS-053 (a Loan__c with principal, rate and tenure)

## Goal

When a loan is disbursed, it gets a full reducing-balance schedule. The EMI is rounded to ₹1, the last row absorbs the rounding, and due dates follow the disbursement day with a day-28 cap (BR-37, BR-39). AC-09 is proved by a unit test.

## Build

**Class `EmiScheduleService`** — `public with sharing class`. PayoutService calls it in LAMS-056. PaymentAllocationService reuses `buildSchedule` in LAMS-058.

| Method | Signature | Notes |
| --- | --- | --- |
| Invocable | `@InvocableMethod(label='Create EMI Schedule') public static void createSchedules(List<Id> loanIds)` | Bulk entry point |
| EMI | `public static Decimal calculateEmi(Decimal principal, Decimal annualRatePct, Integer months)` | Rounded to ₹1, `RoundingMode.HALF_UP` |
| Due date | `public static Date dueDate(Date disbursementDate, Integer instalmentNo)` | BR-37 rule |
| Pure builder | `public static List<EMI_Instalment__c> buildSchedule(Loan__c loan)` | No DML; needs Principal__c, Interest_Rate__c, Tenure__c, Disbursement_Date__c |

**EMI** (r = annual rate ÷ 12 ÷ 100, n = tenure in months):

1. If r = 0: EMI = ROUND(P ÷ n, 0).
2. Else: EMI = ROUND(P · r · (1+r)^n ÷ ((1+r)^n − 1), 0). Compute `(1+r)^n` with `Decimal.pow(n)`. Keep full precision until the final ROUND.

**Schedule** (`buildSchedule`), with opening = P:

1. For k = 1 … n−1: interest = ROUND(opening × r, 0); principal = EMI − interest; closing = opening − principal.
2. Row n (last): principal = opening; interest = ROUND(opening × r, 0); EMI_Amount = principal + interest; closing = 0.
3. Each row: `Loan__c`, `Instalment_No__c` = k, `Due_Date__c` = `dueDate(Disbursement_Date__c, k)`, `EMI_Amount__c`, `Interest_Component__c`, `Principal_Component__c`, `Closing_Balance__c`, `Late_Fee__c` = 0, `Amount_Paid__c` = 0, `Status__c` = Upcoming.

**Due date** (`dueDate`):

1. `Date firstOfMonth = Date.newInstance(d.year(), d.month(), 1).addMonths(k)`
2. Return `Date.newInstance(firstOfMonth.year(), firstOfMonth.month(), Math.min(d.day(), 28))`.
   Examples: disbursed 15 Mar → 15 Apr, 15 May …; disbursed 31 Jan → 28 Feb, 28 Mar … (day 28 every month, not "end of month").

**`createSchedules(loanIds)`:**

1. One query loads the loans plus a sub-query count of existing instalments. Skip any loan that already has instalments (idempotent; retries never duplicate) or has no Disbursement_Date__c.
2. Build all rows into one list. If `rows.size()` exceeds `Limits.getLimitDmlRows() − Limits.getDmlRows()`, throw a custom `EmiScheduleException` (proposed) instead of failing halfway.
3. One `insert` of all rows.
4. Update `Loan__c.EMI_Amount__c` to the rounded EMI where it differs. The copy taken from the application formula keeps paise, for example 8,978.71.

## Steps

1. Write `EmiScheduleService` with the four methods.
2. Write `EmiScheduleServiceTest` with test data from `TestDataFactory`. Add a `createLoan(principal, ratePct, tenure, disbursementDate)` helper (proposed) if it is not there yet.
3. Test cases:
   - **AC-09:** P = 1,00,000, 14%, 12 months → 12 rows; rows 1–11 EMI ₹8,979; row 1 interest ₹1,167, principal ₹7,812, closing ₹92,188; row 12 EMI ₹8,977, interest ₹104, principal ₹8,873, closing ₹0; Σ principal = ₹1,00,000; Σ interest = ₹7,746
   - `calculateEmi(100000, 14, 12)` = 8979
   - Due dates: disbursed 2026-01-31 → row 1 2026-02-28, row 2 2026-03-28; disbursed 2026-03-15 → row 1 2026-04-15
   - Zero rate: P = 1,20,000, 0%, 12 → EMI 10,000, no division error
   - Running twice creates no second schedule
   - Bulk: 200 loans × 12 months in one `createSchedules` call → 2,400 rows; assert ≤ 3 queries and 2 DML statements
   - Rate 9%, 360 months (Home Loan): last row closing 0 and Σ principal = P
4. `sf apex run test --class-names EmiScheduleServiceTest --code-coverage --result-format human --wait 10`
5. Commit: `feat(apex): EmiScheduleService reducing-balance schedule [LAMS-055]`.

## Learn

- **Decimal, not Double, for money.** `Decimal.setScale(0, RoundingMode.HALF_UP)` is deterministic. Double arithmetic can turn 8,978.5 into 8,978.4999.
- **Rounding drift:** rounding each row leaves a few rupees over or short after n rows. Paying off the remaining opening balance on the last row guarantees a closing balance of 0.
- `Date.addMonths` on the 31st clamps to the month end (31 Jan + 1 month = 28/29 Feb). BR-37 caps at 28 instead, so build the date from day 1 of the month and `Math.min(day, 28)`.
- **Governor limits:** 10,000 DML rows per transaction. 200 Home loans × 360 rows = 72,000 rows would fail, which is why the bulk test uses 12-month loans and the service checks the limit first.

## Done when

- [ ] AC-09 passes in `EmiScheduleServiceTest`: 12 rows, EMI ₹8,979, closing balance ₹0 on row 12
- [ ] Due-date tests prove the day-28 cap and the disbursement-day rule
- [ ] Zero-rate, 360-month, idempotency and 200-loan bulk tests pass
- [ ] `EmiScheduleService` coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.6 BR-37, §6.7 BR-39, BR-40, §9 AC-09, §10.6 EMI_Instalment__c and EMI formula, §14 EmiScheduleService, NFR-01, NFR-10
