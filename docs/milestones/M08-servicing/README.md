# M08 – Servicing

≈ 24h · 13 work items · Starts after: [M07 – Documents and approval](../M07-documents-and-approval/README.md)

**Goal:** An accepted offer becomes a loan that is disbursed, scheduled, paid, chased when overdue and closed.

**Exit criteria:** AC-07, AC-08, AC-10 (via test), AC-11, AC-12.

## Work items

Tick items here; the linked file says what to build.

- [ ] [LAMS-053](053-offer-accepted-flow-loanagreement-pdf.md) · Offer Accepted flow + LoanAgreement PDF · `M`
- [ ] [LAMS-054](054-loantrigger-loansharingservice-tests.md) · LoanTrigger + LoanSharingService + tests · `M`
- [ ] [LAMS-055](055-emischeduleservice-tests-ac-09.md) · EmiScheduleService + tests (AC-09) · `M`
- [ ] [LAMS-056](056-payoutservice-disburse-loan-flow-tests.md) · PayoutService + Disburse Loan flow + tests · `L`
- [ ] [LAMS-057](057-emischedule-loansummarycard-lwcs.md) · emiSchedule + loanSummaryCard LWCs · `M`
- [ ] [LAMS-058](058-paymenttrigger-paymentallocationservice-rebuild.md) · PaymentTrigger + PaymentAllocationService (rebuild, advance, payoff, reversal) + tests · `L`
- [ ] [LAMS-059](059-loanoverduebatch-loanoverduescheduler-tests.md) · LoanOverdueBatch + LoanOverdueScheduler + tests · `L`
- [ ] [LAMS-060](060-waive-late-fee-flow.md) · Waive Late Fee flow · `S`
- [ ] [LAMS-061](061-prepayment-quote-flow.md) · Prepayment Quote flow · `S`
- [ ] [LAMS-062](062-send-notification-subflow-remaining-templates.md) · Send Notification subflow + remaining templates · `M`
- [ ] [LAMS-063](063-smsservice-chunked-future-tests.md) · SmsService (chunked @future) + tests · `M`
- [ ] [LAMS-064](064-daily-reminders-scheduled-flow-incl-offer-expiry.md) · Daily Reminders scheduled flow (incl. offer expiry) · `M`
- [ ] [LAMS-065](065-closureletter-pdf.md) · ClosureLetter PDF · `S`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: AC-07, AC-08, AC-10 (via test), AC-11, AC-12.
- [ ] Coverage ≥ 90% for every Apex class added in this milestone
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._
