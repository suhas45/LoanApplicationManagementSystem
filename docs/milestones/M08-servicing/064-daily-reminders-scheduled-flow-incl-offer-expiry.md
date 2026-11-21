# LAMS-064 · Daily Reminders scheduled flow (incl. offer expiry)

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-30, BR-31, BR-55

**Depends on:** LAMS-062 (Send Notification, templates `LAMS_Offer_Expiring`, `LAMS_EMI_Due`), LAMS-048 (Loan Approval process; Offer_Expiry_Date__c stamped at approval), LAMS-017 (Application_Expiry_Days__c, Approval_Reminder_Days__c), LAMS-055 (instalments with due dates)

## Goal

Every morning at 07:00, borrowers are reminded of EMIs due in 3 days and offers expiring in 3 days. Offers past their expiry date and applications idle for 30 days before a decision become Expired, and approvers waiting more than 2 business days get a reminder (BR-30, BR-31, BR-55). This item completes AC-07.

## Build

A schedule-triggered flow runs on one object, so "Daily Reminders" is built as **two** schedule-triggered flows (proposed split), both daily at 07:00. Set the org default time zone to Asia/Kolkata.

**Flow `Daily_Reminders_Applications`**: object `Loan_Application__c`, condition `Status__c` IN (Draft, Submitted, Document Review, Under Review, Approved). It runs one interview per open application. Branches in a Decision, evaluated in this order:

| # | Branch | Condition | Action |
| --- | --- | --- | --- |
| 1 | Offer expired (BR-30, AC-07) | Status = Approved AND `Offer_Expiry_Date__c` < `{!$Flow.CurrentDate}` | Update: Status__c = Expired |
| 2 | Offer expiring (BR-30) | Status = Approved AND `Offer_Expiry_Date__c` = CurrentDate + 3 | Send Notification(`LAMS_Offer_Expiring`, Borrower__c, Id) |
| 3 | Idle expiry (BR-31) | Status in (Draft, Submitted, Document Review, Under Review) AND `BLANKVALUE(Last_Activity_Date__c, CreatedDate)` < NOW() − `{!$Setup.LAMS_Settings__c.Application_Expiry_Days__c}` AND no pending approval (see below) | Update: Status__c = Expired |
| 4 | Approval reminder (BR-55) | Status = Under Review AND pending work item older than `Approval_Reminder_Days__c` business days | Send Custom Notification `LAMS_Approval_Reminder` (proposed) to the work item's ActorId (user or queue), target = application |

Pending approval lookup (branches 3 and 4):

1. Get Records `ProcessInstance` where TargetObjectId = `{!$Record.Id}` and Status = Pending.
2. Get Records `ProcessInstanceWorkitem` where ProcessInstanceId = that Id. This gives ActorId and CreatedDate.

An application with a pending approval is not idle-expired; its approver gets the reminder instead (proposed). Expiring it would need a recall first.

Business days (A5: Mon–Sat) without Apex, as formula `businessDaysWaiting` (proposed; holidays ignored):
`(TODAY() − DATEVALUE(CreatedDate)) − FLOOR(((TODAY() − DATEVALUE(CreatedDate)) + WEEKDAY(DATEVALUE(CreatedDate)) − 1) / 7)`
This is total days minus the Sundays in between. Remind when the result is greater than `Approval_Reminder_Days__c` (2).

**Flow `Daily_Reminders_EMI`**: object `EMI_Instalment__c`, conditions `Status__c` = Upcoming AND `Loan__r.Status__c` = Active.
- Decision: `Due_Date__c` = `{!$Flow.CurrentDate}` + 3 → Send Notification(`LAMS_EMI_Due`, `Loan__r.Borrower__c`, Id) (BR-52).
- To avoid one interview per future instalment, add a formula field `Days_Until_Due__c` = `Due_Date__c − TODAY()` (proposed) and use `Days_Until_Due__c = 3` in the start condition if your org allows formula fields there. Otherwise keep the Decision.

Both flows run as the Automated Process user and read toggles through `$Setup` org defaults. Status changes made by the system do not stamp Last_Activity_Date__c (§10.3).

**Custom notification type** `LAMS_Approval_Reminder` (proposed): desktop and mobile channels. Title and body come from labels: "Application {Name} has waited {n} business days for your approval".

## Steps

1. Set the org time zone. Create the custom notification type and the labels (EN/HI).
2. Build `Daily_Reminders_Applications` and `Daily_Reminders_EMI`. Activate both with start time 07:00, frequency Daily.
3. Prepare demo data:
   - Application A: Approved, Offer_Expiry_Date__c = yesterday
   - Application B: Approved, expiry = today + 3
   - Application C: Draft, Last_Activity_Date__c = 31 days ago
   - Application D: Under Review and submitted for approval. Work item dates cannot be back-dated, so either wait 3 business days or temporarily set Approval_Reminder_Days__c to 0 in lamsSettings
   - An instalment due in 3 days
4. Use Debug in Flow Builder, which can run a scheduled flow against a chosen record, for each record. Then let the 07:00 run happen and check the results the next morning: A Expired, B emailed, C Expired, D approver notified, borrower emailed for the EMI.
5. Check that Respond to Offer (LAMS-052) refuses an Expired application.
6. Retrieve: `sf project retrieve start --metadata Flow:Daily_Reminders_Applications Flow:Daily_Reminders_EMI CustomNotificationType:LAMS_Approval_Reminder`
7. Commit: `feat(flow): Daily Reminders scheduled flows with offer expiry [LAMS-064]`.

## Learn

- **Schedule-triggered flows** run one interview per record that matches the start conditions. The platform processes them in batches of 200 and bulkifies Get Records and subflows across those interviews. A single flow with a big Get Records and a loop would hit SOQL limits inside the subflow calls instead.
- **Offer_Expiry_Date__c is a stamped date, not a formula**, so changing Offer_Validity_Days__c never moves existing offers. The nightly job only compares dates.
- Custom notifications can target users, groups **and queues**, while Tasks cannot be owned by a queue. That makes them the simple way to remind a "Credit Managers" queue approver.
- `<` vs `≤` matters: an offer valid 15 days must still be acceptable on day 15, so expire only when the expiry date is before today.

## Done when

- [ ] AC-07: an offer not accepted 15 days after approval is Expired after the next 07:00 run
- [ ] An offer expiring in 3 days and an EMI due in 3 days each send one email (and SMS when enabled) in the borrower's language
- [ ] A pre-decision application idle for 30 days (Application_Expiry_Days__c) becomes Expired; one with a pending approval is not expired and its approver is notified after 2 business days
- [ ] Both flows are active, scheduled daily at 07:00 IST, and in source
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §5 statuses Expired, §6.5 BR-30, BR-31, §6.9 BR-52, BR-55, §8 A5, C3, §9 AC-07, §10.3 Offer_Expiry_Date__c, Last_Activity_Date__c, §12 Offer_Validity_Days__c, Application_Expiry_Days__c, Approval_Reminder_Days__c, §13.2 Daily Reminders, §13.4 Loan Approval
