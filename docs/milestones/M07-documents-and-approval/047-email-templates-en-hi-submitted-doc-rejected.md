# LAMS-047 · Email templates EN/HI (submitted, doc rejected, approved, rejected)

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** M (2–5h) · **Delivers:** BR-52

**Depends on:** LAMS-038 (Application Submitted flow), LAMS-045 (documents can be rejected), LAMS-046 (router can reject), LAMS-008 (Contact.Preferred_Language__c), LAMS-021 (labels and Hindi translation process)

## Goal

The borrower is emailed, in English or Hindi by Preferred_Language__c, when the application is submitted, a document is rejected, the application is approved (offer) or rejected (BR-52, BR-54, BR-18). These are the first four of the ten templates in §15; the rest come with the Send Notification subflow (LAMS-062), which will replace the inline language choice built here.

## Build

**Folder** `LAMS_Borrower_Emails` (Classic email folder, public read only; proposed).

**Eight Visualforce email templates** — `recipientType="Contact"`, `relatedToType="Loan_Application__c"`; subject and all body text from custom labels; `language="en_US"` in the `_EN` variant and `language="hi"` in `_HI`, so the same labels render translated.

| Template (EN / HI) | Content (merge fields from `relatedTo`) |
| --- | --- |
| `LAMS_Application_Submitted_EN` / `_HI` | Greeting with `recipient.FirstName`; application Name, product, Amount__c, Tenure__c, Submitted_Date__c; "upload your documents in the portal" |
| `LAMS_Document_Rejected_EN` / `_HI` | Application Name; a repeat over `relatedTo.Application_Documents__r` showing each row with Status Rejected: Document_Type__c and Rejection_Reason__c; how to re-upload |
| `LAMS_Application_Approved_EN` / `_HI` | Approved_Amount__c, Interest_Rate__c, Tenure__c, EMI__c, Offer_Expiry_Date__c; accept or decline in the portal (BR-29); the offer letter is on the application (LAMS-051) |
| `LAMS_Application_Rejected_EN` / `_HI` | Rejection_Reason__c (picklist label, translated); contact the branch. Decision_Comments__c is internal and **not** shown |

Use the child relationship name defined in LAMS-010 for the document list. Amounts with `<apex:outputText value="{0, number, ₹#,##,##0}">` (proposed format).

**Labels** (LAMS-021 naming, each translated to Hindi): subject and body labels per template (e.g. `LAMS_Application_Submitted_Subject`, `LAMS_Application_Submitted_Body`), plus a matching SMS text label per event for SmsService (LAMS-063): `LAMS_Application_Submitted_SMS`, `LAMS_Document_Rejected_SMS`, `LAMS_Application_Approved_SMS`, `LAMS_Application_Rejected_SMS` (`{0}` placeholders for application number and amount).

**Eight Email Alerts** on Loan_Application__c, same API names as the templates; recipient **Related Contact: Borrower__c**; From = current user, or an org-wide address *LAMS* if you verify one (proposed).

**Wiring** (each event: Decision on `Borrower__r.Preferred_Language__c` = Hindi → `_HI` alert, else `_EN` alert; *Send Email Alert* action with recordId = the application Id)

| Event | Flow | Change |
| --- | --- | --- |
| Submitted | `Application_Submitted` (LAMS-038) | Element 9 after the status update |
| Document rejected | **`Document_Rejected`** (new, proposed name) | Record-triggered on Application_Document__c, updated, `Status__c Equals Rejected`, only when updated to meet the condition; alert recordId = `{!$Record.Loan_Application__c}` |
| Approved / Rejected | **`Application_Decided`** (new, proposed name) | Record-triggered on Loan_Application__c, updated, formula condition `ISCHANGED({!$Record.Status__c}) && (TEXT({!$Record.Status__c}) = 'Approved' \|\| TEXT({!$Record.Status__c}) = 'Rejected')`; Decision by status → language → alert; also *Publish Loan Event* `Application Approved` / `Application Rejected` (BR-68). LAMS-051 adds the OfferLetter PDF to the Approved branch |

`Application_Decided` is the "record-triggered flow" §13.4 mentions. It sends the approval email for **both** manual approval (LAMS-048) and auto-approve (LAMS-049, which never enters the approval process), so the approval process itself carries no email alert (proposed; see LAMS-048).

## Steps

1. Create the labels and their Hindi translations (Translation Workbench → Translate → Custom Label).
2. Create the folder and the eight VF email templates (Setup → Classic Email Templates → New → Visualforce); test each with *Send Test and Verify Merge Fields* against a demo application.
3. Create the eight Email Alerts.
4. Build `Document_Rejected` and `Application_Decided`; add element 9 to `Application_Submitted`.
5. Setup → Deliverability → Access level *All email* (Developer Edition default may be system email only).
6. Retrieve (list all eight templates and alerts; email templates do not accept wildcards): `sf project retrieve start --metadata EmailFolder:LAMS_Borrower_Emails EmailTemplate:LAMS_Borrower_Emails/LAMS_Application_Submitted_EN WorkflowAlert:Loan_Application__c.LAMS_Application_Submitted_EN Flow:Document_Rejected Flow:Application_Decided Flow:Application_Submitted CustomLabels Translations:hi` (repeat the template and alert entries for the other seven)
7. Write `BorrowerEmailFlowsTest` (flows run without error on every path, both languages).
8. `sf apex run test --class-names BorrowerEmailFlowsTest --code-coverage --result-format human --wait 10`
9. Commit: `feat(notifications): EN/HI templates and alerts for submit, doc rejected, decision [LAMS-047]`.

## Learn

- **Visualforce email templates** are the only Classic template type that can use `{!$Label...}` and a `language` attribute, which is how subjects stay in custom labels (§12).
- **Email alerts can only address fields on their own object** — the rejected-document email is therefore an alert on the application, listing its rejected rows, and the child flow passes the parent Id.
- **One decision flow for one event:** putting the approval email on the status change (not in the approval process) covers manual and automatic approval with one element.
- Developer Edition limits outbound single emails per day; check Email Log Files when a message does not arrive.

## Done when

- [ ] Submitting an application for an English borrower sends the English email; a Hindi borrower gets the Hindi one (subject and body)
- [ ] Rejecting a document emails the borrower with the type and reason; rejecting two documents lists both
- [ ] Approval (by hand in Setup or via LAMS-048/049) sends the offer email with amount, EMI and expiry date; rejection sends the rejection email without internal comments
- [ ] `Application_Decided` publishes Application Approved / Rejected events when Event_Publishing_Enabled__c is on
- [ ] Four `_SMS` labels exist with Hindi translations
- [ ] `BorrowerEmailFlowsTest` passes for both languages and for 200 records updated at once
- [ ] Screenshot of one EN and one HI email in `docs/BRD/images/`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-18, BR-52, BR-53, BR-54, BR-68, §10.1 Preferred\_Language\_\_c, §12 custom labels, §13.2 Send Notification, §13.4 final approval, §15 email templates, NFR-12
