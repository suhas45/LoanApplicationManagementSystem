# LAMS-066 · Loan Event Handler (platform event flow)

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-50

**Depends on:** LAMS-014 (Loan_Event__e), LAMS-036 (LoanEventPublisher), LAMS-059 (LoanOverdueBatch publishes *Loan Overdue*), LAMS-058 (allocation closes the loan), LAMS-062 (Send Notification subflow, EMI Overdue and Loan Closed templates), LAMS-065 (ClosureLetter PDF)

## Goal

React to published business events inside Salesforce: a *Loan Overdue* event creates one follow-up Task for the assigned Operations Officer and notifies the borrower (BR-50, AC-11 task part); a *Loan Closed* event generates the closure letter and emails it (BR-46).

## Build

**Flow `Loan_Event_Handler`** — label *Loan Event Handler*; type Platform Event–Triggered Flow; object `Loan_Event__e`. It runs as the **Automated Process** user (BRD C3).

| Element | Type | Details |
| --- | --- | --- |
| Get Loan | Get Records | `Loan__c` where `Id = {!$Record.Record_Id__c}`; first record; fields Name, Borrower__c, Assigned_Officer__c, Overdue_Bucket__c, Days_Past_Due__c |
| Loan found? | Decision | Stop (end) if no loan; the event may refer to a deleted or wrong record |
| Event type | Decision | Outcomes on `{!$Record.Event_Type__c}`: **Loan Overdue**, **Loan Closed**; default = end (all other event types are for external subscribers only) |
| *Loan Overdue →* Open task today? | Get Records + Decision | `Task` where WhatId = loan, Status ≠ Completed, Subject = the overdue subject below, CreatedDate = TODAY. If found, skip creation (events can be redelivered; AC-11 wants exactly one task) |
| Create Follow-up Task | Create Records | OwnerId = `Assigned_Officer__c`; WhatId = loan; Subject = label `LAMS_Task_Overdue_Subject` (proposed) + Name + bucket; ActivityDate = TODAY + 1 (O4: task within 1 day); Priority = High when bucket is Watch, Substandard or Critical, else Normal |
| Notify borrower | Subflow `Send_Notification` | template = EMI Overdue; recipient = `Borrower__c`; record = loan |
| *Loan Closed →* Closure letter | Action | The ClosureLetter invocable from LAMS-065 (it must render the PDF in a Queueable, see Learn) |
| Email borrower | Subflow `Send_Notification` | template = Loan Closed; recipient = `Borrower__c`; record = loan |
| Fault paths | Fault connectors | Every Create/Action fault goes to one *Notify Admin* Send Email action with `{!$Flow.FaultMessage}` and the loan Id, then ends; never leave a fault path unconnected |

Event type values come from LAMS-036; the two used here are the names in BRD §13.2: `Loan Overdue`, `Loan Closed`.

**Test class `LoanEventHandlerFlowTest`** (proposed name): publish `Loan_Event__e` with `EventBus.publish`, then `Test.getEventBus().deliver()`, then assert.

## Steps

1. In Flow Builder: New Flow → Platform Event–Triggered Flow → object *Loan Event*. Build the elements above; keep labels in custom labels.
2. Save as `Loan_Event_Handler`, activate.
3. Write `LoanEventHandlerFlowTest`:
   - Overdue event for a loan with an Assigned Officer → exactly 1 Task owned by that officer.
   - Same event published twice → still 1 Task.
   - Loan Closed event → closure letter file linked to the loan (or the Queueable enqueued) and a Send Notification call.
   - Other event type (e.g. Loan Disbursed) → no Task.
   - Bulk: 200 Overdue events for 200 loans in one `deliver()` → 200 Tasks, no limit errors.
4. Manual check: run `LoanOverdueBatch` (LAMS-059) on a demo loan 6 days overdue; confirm the Task and email (AC-11).
5. Retrieve: `sf project retrieve start --metadata Flow:Loan_Event_Handler`
6. Commit: `feat(flow): Loan Event Handler platform event flow [LAMS-066]`.

## Learn

- **Platform event–triggered flows run as the Automated Process user**, not the publisher. Set Task OwnerId explicitly, and make sure emails from this context use an org-wide email address (LAMS-062), or they fail.
- **Events are delivered at least once and asynchronously.** Make subscribers idempotent (the "open task today?" check) and never assume the subscriber sees the publisher's uncommitted data. LoanEventPublisher publishes *after commit*, so the loan is always there.
- `PageReference.getContentAsPDF()` is not allowed in trigger context; a platform event subscriber is trigger context, so the closure letter must render in a Queueable.
- In Apex tests, events are only delivered when you call `Test.getEventBus().deliver()` (or at `Test.stopTest()`).

## Done when

- [ ] `Loan_Event_Handler` is active in the org and in `force-app/main/default/flows/`
- [ ] AC-11 (task part): a nightly run on an instalment 6 days overdue creates **one** Task for the Assigned Officer, and the borrower gets the EMI Overdue email in their language
- [ ] A Loan Closed event produces a ClosureLetter file on the loan and a Loan Closed email
- [ ] `LoanEventHandlerFlowTest` passes, including the duplicate-event and 200-event bulk cases
- [ ] With `Event_Publishing_Enabled__c` off no event is published, and the README notes that overdue tasks then depend on the event toggle (see References)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §13.2 Loan Event Handler, §10.10 Loan_Event__e, §14 LoanEventPublisher and LoanOverdueBatch, §8 C3, BR-46, BR-50, BR-68, AC-11
