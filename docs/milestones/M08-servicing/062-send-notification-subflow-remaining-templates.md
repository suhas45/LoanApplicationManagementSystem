# LAMS-062 · Send Notification subflow + remaining templates

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-52, BR-54

**Depends on:** LAMS-047 (first four EN/HI templates and the template style), LAMS-008 (Contact.Preferred_Language__c), LAMS-021 (custom labels + Hindi translations), LAMS-056 (Disbursement_Status__c = Disbursed is set)

## Goal

One reusable subflow sends every borrower email and picks the English or Hindi template from the borrower's preferred language (BR-52, BR-54). The six templates not built in M07 are added in both languages, so all ten §15 templates exist.

## Build

**Autolaunched flow `Send_Notification`** (label *Send Notification*). Every caller uses it as a subflow.

| Input variable | Type | Example |
| --- | --- | --- |
| `templateName` | Text | Base name without language suffix, e.g. `LAMS_Loan_Disbursed` |
| `recipientId` | Text | Borrower Contact Id |
| `recordId` | Text | Record the template merges from (loan, application, instalment, Case) |

Elements:

1. **Get Records** `Contact` = recipientId (Email, Preferred_Language__c, MobilePhone).
2. **Decision:** Email blank → skip to the SMS branch.
3. **Formula** `templateDevName` = `{!templateName} & IF(ISPICKVAL({!contact.Preferred_Language__c}, "Hindi"), "_HI", "_EN")`.
4. **Get Records** `EmailTemplate` where DeveloperName = templateDevName. If none is found, get `{!templateName}_EN` (fallback).
5. **Action *Send Email*:** Email Template ID = template Id, Recipient ID = recipientId, Related Record ID = recordId, Sender Type = OrgWideEmailAddress (`LAMS Notifications`, proposed), Log Email on Send = true (audit, O6).
6. **SMS branch (placeholder):** a Decision on `{!$Setup.LAMS_Settings__c.SMS_Enabled__c}` with an empty "on" path. LAMS-063 adds the *Send SMS* action there (BR-53).
7. A fault path on the Send Email action writes a Task for the record owner (label `LAMS_Task_Notification_Failed`, proposed). The caller's transaction is never rolled back by a failed email.

**Email templates in this item**: 6 events × 2 languages = 12. Use the same type as LAMS-047 (Visualforce email templates, so `relatedTo.Loan__r.Name` and `{!$Label…}` work), in folder `LAMS_Notifications` (proposed). `recipientType="Contact"`. The EN template sets `language="en_US"` and the HI template `language="hi"`, and subject and body lines come from custom labels (proposed prefix `LAMS_Email_<Event>_`), so the Hindi template renders the Translation Workbench text (§12).

| §15 template | DeveloperNames | relatedToType | Key merge fields |
| --- | --- | --- | --- |
| Offer Expiring | `LAMS_Offer_Expiring_EN` / `_HI` | Loan_Application__c | Name, Approved_Amount__c, Offer_Expiry_Date__c, portal link |
| Loan Disbursed | `LAMS_Loan_Disbursed_EN` / `_HI` | Loan__c | Name, Net_Disbursement__c, Disbursement_Date__c, Disbursement_Reference__c, EMI_Amount__c, Next_Due_Date__c |
| EMI Due | `LAMS_EMI_Due_EN` / `_HI` | EMI_Instalment__c | Loan__r.Name, Instalment_No__c, Due_Date__c, Balance_Due__c |
| EMI Overdue | `LAMS_EMI_Overdue_EN` / `_HI` | Loan__c | Name, Overdue_Amount__c, Days_Past_Due__c, late-fee rule |
| Loan Closed | `LAMS_Loan_Closed_EN` / `_HI` | Loan__c | Name, Closure_Type__c, Total_Paid__c; closure letter is on My Loans (LAMS-065) |
| Prepayment Quote | `LAMS_Prepayment_Quote_EN` / `_HI` | Case | CaseNumber, Loan__r.Name, Prepayment_Quote_Amount__c, quote date, validity note (LAMS-061) |

**Who calls Send Notification** (BR-52):

| Event | Caller | Item |
| --- | --- | --- |
| Submitted, document rejected, approved, rejected | The M07 flows; switch any direct email alert to this subflow so the language rule applies | LAMS-047/048 |
| Offer expiring, EMI due in 3 days | Daily Reminders | LAMS-064 |
| Disbursed | New record-triggered flow `Loan_Disbursed_Notification` (proposed) on Loan__c, after save, when `Disbursement_Status__c` changes to Disbursed → Send Notification(`LAMS_Loan_Disbursed`, Borrower__c, Id) | this item |
| EMI overdue, loan closed | Loan Event Handler | LAMS-066 |
| Prepayment quote | Prepayment Quote | LAMS-061 |

## Steps

1. Create Org-Wide Email Address *LAMS Notifications* and verify it. Set Setup → Deliverability → Access level = All email.
2. Add the `LAMS_Email_*` labels and translate them to Hindi in Translation Workbench.
3. Create the 12 templates in the folder and preview each against a demo record.
4. Build `Send_Notification` and `Loan_Disbursed_Notification`. Debug Send Notification once with a Hindi and once with an English demo borrower.
5. Retrieve: `sf project retrieve start --metadata Flow:Send_Notification Flow:Loan_Disbursed_Notification EmailTemplate:LAMS_Notifications/* CustomLabels Translations:hi`
6. Commit: `feat(notifications): Send Notification subflow and 12 EN/HI templates [LAMS-062]`.

## Learn

- **Subflows** keep the language rule in one place. Each caller passes three values and never chooses a template itself.
- **Approval-process email alerts use one fixed template** and cannot choose by Preferred_Language__c. Send borrower emails from flows instead.
- **Developer Edition email limits are tiny** (a few external emails per day). Point demo borrowers at your own inbox and watch Setup → Email Log Files when something does not arrive.
- Scheduled and platform-event flows run as the Automated Process user, which has no email address of its own. Without an Org-Wide Email Address as sender, the send fails.

## Done when

- [ ] All 10 §15 templates exist in `_EN` and `_HI` versions (6 from this item, 4 from LAMS-047) and are in source
- [ ] A Hindi-preference borrower receives the Hindi template; an English one the English template; a missing HI template falls back to EN
- [ ] Disbursing a loan sends the Loan Disbursed email once
- [ ] A borrower with no email causes no error in the calling flow
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.9 BR-52 – BR-54, §10.1 Preferred_Language__c, §12 custom labels, §13.2 Send Notification, §15 email templates (English and Hindi), C3, NFR-12
