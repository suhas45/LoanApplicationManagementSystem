# LAMS-059 · LoanOverdueBatch + LoanOverdueScheduler + tests

**Milestone:** [M08 – Servicing](README.md) · **Size:** L (5–10h) · **Delivers:** BR-48 – BR-50

**Depends on:** LAMS-058 (allocation must be right before overdue is judged; reuses `statusFor` and `daysPastDue`), LAMS-055 (schedules), LAMS-036 (LoanEventPublisher), LAMS-019 (FeatureToggle: Late_Fees_Enabled__c)

## Goal

Every night, instalments past their due date become Overdue. After the product's grace days, a late fee of 2% of the unpaid EMI is added once per month overdue. Each loan's days past due is set, and a *Loan Overdue* event is published when the bucket changes (BR-48 – BR-50, AC-11).

## Build

**New field (proposed)** `EMI_Instalment__c.Late_Fee_Charges__c`: Number(3,0), default 0. It counts the monthly fees already added, so a re-run on the same night never charges twice (NFR-08). Add it to the LAMS-013 object source and update §10.6 in the BRD.

**Class `LoanOverdueBatch`** — `public with sharing class LoanOverdueBatch implements Database.Batchable<SObject>`.

| Member | Signature / value |
| --- | --- |
| Constructors | `public LoanOverdueBatch()` (asOf = today) · `@TestVisible LoanOverdueBatch(Date asOf)` |
| start | `Database.QueryLocator` over `SELECT Id, Days_Past_Due__c, Assigned_Officer__c, Loan_Product__r.Late_Fee__c, Loan_Product__r.Grace_Days__c FROM Loan__c WHERE Status__c = 'Active'` |
| execute | `execute(Database.BatchableContext bc, List<Loan__c> scope)` with a batch size of 200 |
| finish | Nothing to do (optionally log the job summary) |

`execute` algorithm:

1. One query: instalments for the scope loans with `Due_Date__c <= :asOf AND Status__c NOT IN ('Paid','Cancelled')`, ordered by Loan__c, Due_Date__c. Only due rows are read, not the whole 60,000-row schedule (NFR-01).
2. For each row, set daysPast = `Due_Date__c.daysBetween(asOf)`, then:
   1. **Status:** `PaymentAllocationService.statusFor(row, asOf)`, which gives Due on the due date and Overdue after it.
   2. **Late fee** applies only if `Late_Fees_Enabled__c` is on (FeatureToggle), the row is not `Late_Fee_Waived__c` (proposed: a waiver stops further fees on that row), and daysPast > grace (`Grace_Days__c`, default 5):
      - charges due m = FLOOR((daysPast − grace − 1) ÷ 30) + 1 (day 6 → 1, day 36 → 2, day 66 → 3; one month = 30 days, proposed)
      - for each missing charge (m − Late_Fee_Charges__c): fee = ROUND(MIN(EMI_Amount__c, unpaid balance) × Late_Fee__c ÷ 100, 0). Add it to Late_Fee__c and add 1 to Late_Fee_Charges__c.
3. **Per loan:** newDpd = `PaymentAllocationService.daysPastDue(rows, asOf)` (0 when the loan has no Overdue rows). Loans in the scope with no rows also get 0.
4. **Bucket**, worked out in Apex with `bucketFor(Integer dpd)` (proposed), because the Overdue_Bucket__c formula is stale in memory:

| DPD | Bucket |
| --- | --- |
| 0 | Current |
| 1 – 30 | Soft |
| 31 – 60 | Watch |
| 61 – 90 | Substandard |
| > 90 | Critical |

5. If `bucketFor(newDpd)` ≠ `bucketFor(old Days_Past_Due__c)` and the new bucket is worse (proposed: an improvement creates no task), publish one `Loan_Event__e` per loan via LoanEventPublisher: Event_Type__c = *Loan Overdue*, Record_Id__c = loan Id, Loan_Number__c, Amount__c = overdue amount, Payload__c = `{"bucket":…, "dpd":…}`. The Loan Event Handler (LAMS-066) turns it into the Task for Assigned_Officer__c and the borrower's EMI Overdue notice (BR-50).
6. DML: one update of changed instalments, one update of loans whose Days_Past_Due__c changed.

The batch only publishes an event. It does not send SMS or email itself, because a batch cannot call `@future` (SmsService).

**Class `LoanOverdueScheduler`** — `public with sharing class LoanOverdueScheduler implements Schedulable`. `execute(SchedulableContext sc)` calls `Database.executeBatch(new LoanOverdueBatch(), 200)`.
Schedule it nightly at 01:30 IST (proposed; before Daily Reminders at 07:00):
`System.schedule('LAMS Loan Overdue Nightly', '0 30 1 * * ?', new LoanOverdueScheduler());`
Put this line in `scripts/apex/schedule-jobs.apex` (proposed) next to the LAMS-020 post-deploy script.

## Steps

1. Add `Late_Fee_Charges__c` and deploy it.
2. Write `LoanOverdueBatch` (with `bucketFor`) and `LoanOverdueScheduler`.
3. Write `LoanOverdueBatchTest`, using the AC-09 loan with grace 5 and late fee 2%, run as `Test.startTest(); Database.executeBatch(new LoanOverdueBatch(asOf), 200); Test.stopTest();`:
   - **AC-11:** row 1 is 6 days past due and unpaid → Status Overdue, Late_Fee__c = ₹180 (2% × ₹8,979 = 179.58 → ₹180), Late_Fee_Charges__c 1, Days_Past_Due__c 6, bucket Soft, exactly one *Loan Overdue* event (assert with the LoanEventPublisher test hook from LAMS-036)
   - run again with the same asOf → fee still ₹180, no second event
   - 4 days past due → Overdue, no fee (grace), DPD 4, Soft
   - 36 days → second charge (₹360 total), bucket Watch, event published
   - toggle Late_Fees_Enabled__c off → status and DPD still set, Late_Fee__c 0
   - waived row → no fee added
   - a row paid in full → not touched; a loan back to DPD 0 → bucket Current, no event
   - bulk: 200 Active loans, each with one overdue row → 200 fees, 200 events, one execute
   - scheduler: `System.schedule('t', '0 30 1 * * ?', new LoanOverdueScheduler())` → a CronTrigger exists with that expression
4. `sf apex run test --class-names LoanOverdueBatchTest --code-coverage --result-format human --wait 10`
5. Schedule in the org: `sf apex run --file scripts/apex/schedule-jobs.apex`; check Setup → Scheduled Jobs.
6. Commit: `feat(apex): LoanOverdueBatch and nightly scheduler [LAMS-059]`.

## Learn

- **Batch + Schedulable:** the Schedulable only starts the batch. The cron expression `sec min hour day-of-month month day-of-week` runs in the scheduling user's time zone, so schedule it as a user set to Asia/Kolkata.
- **Batch per loan, not per instalment:** each `execute` gets fresh governor limits for 200 loans. Splitting a loan's rows across chunks would give two different DPD values.
- **Idempotent nightly jobs:** a counter (Late_Fee_Charges__c) instead of "charge on day 6 exactly" means a missed or repeated night is fixed by the next run (NFR-08).
- `@future` cannot be called from batch Apex, and a batch cannot start another `@future` chain. Publishing a platform event hands the follow-up to a separate transaction.

## Done when

- [ ] AC-11 batch part: an instalment 6 days overdue with 5 grace days gets the ₹180 late fee and bucket Soft, and exactly one Loan Overdue event is published (test passes). The single officer Task is asserted once LAMS-066 consumes the event
- [ ] Re-running the same night adds no second fee and no second event
- [ ] Toggle on/off, grace, second-month, waived, bulk-200 and scheduler tests pass; coverage ≥ 90% for both classes
- [ ] The job "LAMS Loan Overdue Nightly" is scheduled in the org
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §5 late fee and grace period, §6.8 BR-48 – BR-50, §9 AC-11, §10.5 Days_Past_Due__c, Overdue_Bucket__c, §10.6 Late_Fee__c, §12 Late_Fees_Enabled__c, §13.2 Loan Event Handler, §14 LoanOverdueBatch + LoanOverdueScheduler, NFR-01, NFR-08
