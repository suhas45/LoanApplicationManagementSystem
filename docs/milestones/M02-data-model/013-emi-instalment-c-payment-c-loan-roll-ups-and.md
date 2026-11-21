# LAMS-013 · EMI_Instalment__c, Payment__c, loan roll-ups and formulas

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** §10.6, §10.7

**Depends on:** LAMS-012 (Loan__c)

## Goal

A loan has its EMI schedule rows (BR-39, BR-40) and its payments (BR-41, BR-45), and the loan summarises them: total paid, principal repaid, outstanding principal, overdue amount and next due date. Allocation (LAMS-058), the overdue batch (LAMS-059) and the portfolio dashboard (BR-63) then work from fields, not ad-hoc queries.

## Build

**Object `EMI_Instalment__c`** — label *EMI Instalment*; Name = Auto Number `EMI-{0000000}` (proposed); enable Reports.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan__c | Master-Detail(Loan__c) | Sharing setting Read/Write; related list *EMI Schedule*; child relationship `EMI_Instalments` |
| Instalment_No__c | Number(3,0) | Required |
| Due_Date__c | Date | Required |
| EMI_Amount__c | Currency(16,2) | Last row absorbs rounding (LAMS-055) |
| Interest_Component__c | Currency(16,2) | |
| Principal_Component__c | Currency(16,2) | |
| Closing_Balance__c | Currency(16,2) | |
| Late_Fee__c | Currency(16,2) | Default 0. Added nightly after grace days |
| Late_Fee_Waived__c | Checkbox | Default false (BR-51) |
| Waiver_Reason__c | Text(255) | |
| Amount_Paid__c | Currency(16,2) | Default 0. Written only by allocation |
| Principal_Paid__c | Formula (Currency, 2 dp) | `MIN(BLANKVALUE(Principal_Component__c, 0), MAX(0, BLANKVALUE(Amount_Paid__c, 0) - BLANKVALUE(Late_Fee__c, 0) - BLANKVALUE(Interest_Component__c, 0)))` |
| Balance_Due__c | Formula (Currency, 2 dp) | `IF(ISPICKVAL(Status__c, "Cancelled"), 0, BLANKVALUE(EMI_Amount__c, 0) + BLANKVALUE(Late_Fee__c, 0) - BLANKVALUE(Amount_Paid__c, 0))`. The Cancelled branch is proposed, so cancelled rows never show a balance |
| Status__c | Picklist (restricted) | Upcoming (default), Due, Partly Paid, Paid, Overdue, Cancelled |
| Paid_Date__c | Date | |

**Object `Payment__c`** — label *Payment*; Name = Auto Number `PAY-{0000000}` (proposed); enable Reports.

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan__c | Master-Detail(Loan__c) | Sharing setting **Read Only** (creating a payment needs only read on the loan, §11); related list *Payments*; child relationship `Payments` |
| Amount__c | Currency(16,2) | Required |
| Payment_Date__c | Date (proposed type) | Required; default `TODAY()` |
| Mode__c | Picklist (restricted) | Online, Auto-Debit, Bank Transfer, Cash. Required (proposed) |
| Reference__c | Text(50) | Required, Unique (case-insensitive), External ID. Blocks duplicates (BR-41, AC-10) |
| Status__c | Picklist (restricted) | Success (default, proposed), Failed, Reversed |
| Reversal_Reason__c | Text(255) | |

Locking rules (Amount > 0; Amount, Loan, Reference unchangeable after insert) are validation rules in LAMS-032.

**Fields on `Loan__c`**

| Field (API name) | Type | Definition |
| --- | --- | --- |
| Total_Paid__c | Roll-Up Summary (SUM) | Payment__c.Amount__c where `Status__c = Success` |
| Principal_Repaid__c | Roll-Up Summary (SUM) | EMI_Instalment__c.Principal_Paid__c (no filter) |
| Outstanding_Principal__c | Formula (Currency, 2 dp) | `Principal__c - Principal_Repaid__c` |
| Overdue_Amount__c | Roll-Up Summary (SUM) | EMI_Instalment__c.Balance_Due__c where `Status__c = Overdue` |
| Next_Due_Date__c | Roll-Up Summary (MIN) | EMI_Instalment__c.Due_Date__c where `Status__c` not equal to `Paid, Cancelled` |

**Also:** *EMI Schedule* related list on the Loan layout (No, Due Date, EMI, Principal, Interest, Late Fee, Amount Paid, Balance Due, Status) sorted by Instalment_No__c; *Payments* related list (Name, Date, Amount, Mode, Reference, Status).

## Steps

1. Create both objects, Master-Detail field first. Set Payment__c's Master-Detail sharing setting to *Read Only*.
2. Create the remaining fields and the two formulas on EMI_Instalment__c.
3. Create the four roll-ups and the formula on Loan__c.
4. Update the Loan layout.
5. Test by hand with the worked example below.
6. Retrieve:
   `sf project retrieve start --metadata CustomObject:EMI_Instalment__c CustomObject:Payment__c CustomField:Loan__c.Total_Paid__c CustomField:Loan__c.Principal_Repaid__c CustomField:Loan__c.Outstanding_Principal__c CustomField:Loan__c.Overdue_Amount__c CustomField:Loan__c.Next_Due_Date__c "Layout:Loan__c-Loan Layout"`
7. Commit: `feat(data-model): EMI_Instalment__c, Payment__c and loan roll-ups [LAMS-013]`.

**Worked example** (AC-09 loan: Principal 1,00,000, 14%, 12 months, EMI 8,979)

| Row | Due | EMI | Interest | Principal | Closing | Late fee | Paid | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | month 1 | 8,979 | 1,167 | 7,812 | 92,188 | 0 | 8,979 | Paid |
| 2 | month 2 | 8,979 | 1,076 | 7,903 | 84,285 | 179.58 | 0 | Overdue |
| 3 | month 3 | 8,979 | 983 | 7,996 | 76,289 | 0 | 0 | Upcoming |

Add one Success payment of 8,979 with reference `TEST-001`. Expected on the loan: Total_Paid__c 8,979; Principal_Repaid__c 7,812; Outstanding_Principal__c 92,188; Overdue_Amount__c 9,158.58; Next_Due_Date__c = row 2's due date.

## Learn

- **Roll-ups can sum formula fields** only when the formula uses fields on the same record and no `TODAY()`/`NOW()`; Principal_Paid__c and Balance_Due__c qualify.
- **Master-Detail sharing setting** (*Read Only* vs *Read/Write*) sets how much access on the master a user needs to create or edit a detail. The Integration User can post payments to any loan it can read (§11).
- **Allocation writes one field.** Only Amount_Paid__c is written by Apex; everything else (principal paid, balance due, loan totals) is derived, so a full re-allocation (BR-45) cannot leave totals out of step.
- An object can be the master of several detail objects; each detail can have at most two masters.

## Done when

- [ ] Both objects, all fields and the five Loan__c fields exist in the org and in source
- [ ] The worked example gives exactly the expected loan values
- [ ] Marking row 3 Cancelled sets its Balance_Due__c to 0; marking row 2 Paid then makes Next_Due_Date__c blank (no open rows left)
- [ ] A second payment with reference `TEST-001` (or `test-001`) fails on the unique check
- [ ] Setting the payment to Reversed drops Total_Paid__c to 0
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.5 (roll-ups and Outstanding_Principal__c), §10.6 EMI_Instalment__c, §10.7 Payment__c; §11 OWD (Payment__c Read Only); §21 Roll-up summaries; BR-39 – BR-45, BR-48, BR-51, BR-63; AC-09, AC-10
