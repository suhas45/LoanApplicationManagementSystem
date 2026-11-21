# LAMS-096 · Lead queues, assignment rules, matching and duplicate rules

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** M (2–5h) · **Delivers:** BR-84, BR-86

**Depends on:** LAMS-095 (Lead fields, statuses, TestDataFactory lead helpers), LAMS-022 (roles), LAMS-029 (Priya Sharma with LAMS_Sales_Access), LAMS-008 (Contact PAN__c and its matching rule), LAMS-016 (demo borrowers to match against), LAMS-026 (Lead OWD Private)

## Goal

A new lead lands with the right owner, without anyone touching it. Assignment goes by product first, then by city, to a lead queue or a named Loan Officer, and the new owner gets an email (BR-84). Leads still New after one business day appear in a follow-up list (BR-84). A lead whose PAN or mobile matches another lead or an existing borrower Contact is flagged before it is saved. The user can still save it and resolves it as a duplicate or converts it into the existing borrower (BR-86). The queue part of **AC-17** (a Pune Home Loan callback goes to the secured-loan queue) is proven here.

## Build

**Queues** (Setup → Queues)

| Queue (API name) | Label | Supported object | Members | Queue email |
| --- | --- | --- | --- | --- |
| `Leads_Retail` | Leads – Retail | Lead | User: Priya Sharma | Blank; *Send Email to Members* on |
| `Leads_Secured` | Leads – Secured | Lead | User: Priya Sharma | Same |

Members are named **users who hold `LAMS_Sales_Access`** (proposed), not the Loan Officer role. A queue member without Lead access can't open the leads, and a Platform-licence Loan Officer can't be given that access (BRD v2.3, D6). The demo has one such user, because the org has two full Salesforce licences: the admin and Priya Sharma. Both queues therefore have the same member. In a real bank, each queue would map to its own team.

**Helper fields on Lead**

| Field (API name) | Type | Formula | Why |
| --- | --- | --- | --- |
| `Product_Code__c` (proposed) | Formula (Text) | `Loan_Product__r.Product_Code__c` | Assignment criteria, list views and reports compare a code (PL, HL, AL, BL), never a record Id |
| `First_Contact_Overdue__c` (proposed) | Formula (Checkbox) | `AND(ISPICKVAL(Status, "New"), NOW() > CreatedDate + IF(WEEKDAY(DATEVALUE(CreatedDate)) = 7, 2, 1))` | "Not contacted within 1 business day" (BR-84). Business days are Mon–Sat (A5): a lead created on Saturday is due on Monday. Calendar time is an approximation, like the reminders in B37 |

**Assignment rule** *LAMS Lead Assignment* (Setup → Lead Assignment Rules), active. Rule entries run in order and the first match wins.

| Order | Criteria | Assign to | Email template |
| --- | --- | --- | --- |
| 1 | `Product_Code__c` equals `HL,BL` | Queue Leads – Secured | LAMS_Lead_Assigned |
| 2 | `Product_Code__c` equals `PL,AL` AND `City` equals `Mumbai` | User Priya Sharma (org-specific; note it in the README) | LAMS_Lead_Assigned |
| 3 | (no criteria: catch-all, including leads without a product) | Queue Leads – Retail | LAMS_Lead_Assigned |

Entry 2 is the city example (proposed city). If your rule editor won't list the formula field, use *formula evaluates to true* with `Product_Code__c = "PL" || Product_Code__c = "AL"` instead. With a second Loan Officer licence, add a Pune → Rahul Verma entry before entry 3.

**Email template** `LAMS_Lead_Assigned` (Classic Text, folder *LAMS Internal Templates*, proposed; English, because staff use English, LAMS-029). Assignment rules accept only Classic templates.

```
Subject: New lead: {!Lead.Name} – {!Lead.Product_Code__c} {!Lead.Requested_Amount__c}
A new lead has been assigned to you or your queue.
Name: {!Lead.Name}    Mobile: {!Lead.MobilePhone}    City: {!Lead.City}
Product: {!Lead.Loan_Product__c}  Amount: {!Lead.Requested_Amount__c}  Tenure: {!Lead.Requested_Tenure__c} months
Source: {!Lead.LeadSource}
Please call within one business day: {!Lead.Link}
```

Every assignment email counts toward the org's daily email allowance, which is about 15 single emails a day in `Lams`. Keep demo leads to a handful a day.

**Lead Settings:** *Default Lead Owner* = queue Leads – Retail, with *Notify Default Lead Owner* on. This owner catches Web-to-Lead and API leads when no rule runs. It is an org setting; record it in the README.

**Sharing for queue-owned leads (proposed).** Queue members see queue-owned leads. Someone above them in the role hierarchy may not, and Lead is Private (LAMS-026). Add two owner-based sharing rules: *Leads owned by queue Leads – Retail* and *… Leads – Secured* → Role **Credit Head**, Read Only (`Retail_Lead_Queue_to_Credit_Head`, `Secured_Lead_Queue_to_Credit_Head`). They matter for a real Credit Head user and are harmless for the admin who plays that role in `Lams`.

**List views on Lead**

| List view (API name) | Filter | Columns | Visible to |
| --- | --- | --- | --- |
| My Open Leads (`LAMS_My_Open_Leads`) | My leads; Status in New, Contacted, Qualified | Name, Company, Product Code, Requested Amount, City, Status, Created Date | All users |
| Leads Awaiting First Contact (`LAMS_Awaiting_First_Contact`) | All leads; First_Contact_Overdue__c = true | Name, Owner, Product Code, City, Lead Source, Mobile, Created Date | Roles and subordinates: Credit Head (proposed) |
| Leads – Retail, Leads – Secured | Created automatically with each queue | Add Product Code, City, Created Date | Queue members |

**Matching rules** (Setup → Matching Rules; activate each and wait for *Active*)

| Rule (API name) | Object | Criteria | Logic | Match blank fields |
| --- | --- | --- | --- | --- |
| `LAMS_Lead_PAN_Or_Mobile` | Lead | 1 PAN__c Exact · 2 MobilePhone Exact | 1 OR 2 | Off |
| `LAMS_Contact_PAN_Or_Mobile` | Contact | 1 PAN__c Exact · 2 MobilePhone Exact | 1 OR 2 | Off |

Matching works because both sides store one format: Lead mobiles are normalised to `+91XXXXXXXXXX` (LAMS-095), and seed and portal Contacts use the same (LAMS-016).

**Duplicate rule** `LAMS_Lead_Duplicate` (label *LAMS Lead Duplicate*) on Lead

| Setting | Value |
| --- | --- |
| Record-level security | *Bypass sharing rules*. Leads are Private, so a Loan Officer must be warned about a match they can't see |
| Action on create | **Allow**, Alert on, Report on |
| Action on edit | Allow, Alert on, Report on |
| Alert text (label `LAMS_Lead_Duplicate_Alert`, ≤ 255 characters) | "A lead or borrower with this PAN or mobile already exists. Review the matches: if it is the same person, mark this lead Unqualified – Duplicate, or convert it into the existing borrower." |
| Matching rule 1 | Compare Leads with **Leads**: `LAMS_Lead_PAN_Or_Mobile` |
| Matching rule 2 | Compare Leads with **Contacts**: `LAMS_Contact_PAN_Or_Mobile`. Field mapping Lead.PAN__c → Contact.PAN__c, Lead.MobilePhone → Contact.MobilePhone |
| Conditions | None |
| Active | Yes |

**"Allow save with a reason" (proposed reading of BR-86).** The platform has no field for an override reason. The officer records the outcome instead: either *Unqualified* with Unqualified_Reason__c = Duplicate, or conversion, which reuses the existing Contact with that PAN (LAMS-098). *Report on* writes a Duplicate Record Set for every flagged lead, so the flags remain auditable. Leave the org's *Standard Lead Duplicate Rule* (name, email, company) active.

Add the **Potential Duplicates** component to `LAMS_Lead_Record_Page` (LAMS-095) above Details.

**Tests `LeadRoutingTest`** (proposed). Assignment and duplicate rules are org configuration, but they run inside Apex tests when the DML asks for them.

| Test | Arrange | Assert |
| --- | --- | --- |
| `ac17_homeLoanPuneGoesToSecuredQueue` | HL lead, City Pune, ₹40,00,000, 240 months, inserted with `TestDataFactory.insertLeads(leads, true)` | OwnerId = Id of Group `Leads_Secured` (queried by DeveloperName) |
| `personalMumbaiGoesToOfficer` | PL lead, City Mumbai | OwnerId = `TestDataFactory.loanOfficer().Id` (the LAMS_Sales_Access holder) |
| `catchAllGoesToRetailQueue` | PL Delhi, and a lead without a product | Owner = `Leads_Retail` |
| `bulk200` | 200 mixed leads, one insert | Every owner matches its entry; no limit errors |
| `duplicateOfBorrowerIsFlagged` | `TestDataFactory.createBorrower('AAAPS1001A')`; lead with that PAN, inserted with `allowSave = false` | `SaveResult` fails with a `Database.DuplicateError` whose match is on Contact |
| `duplicateCanBeSaved` | Same lead with `allowSave = true` | Saved |
| `sameMobileAsLeadIsFlagged` | Two leads with the same mobile, the second without allowSave | DuplicateError, match on Lead |
| `overdueAfterOneBusinessDay` | New lead; `Test.setCreatedDate(id, Datetime.now().addDays(-2))` | First_Contact_Overdue__c = true; after Status = Contacted it is false |

## Steps

1. Create the two queues.
2. Create `Product_Code__c` and `First_Contact_Overdue__c`; add both to the LAMS Lead Layout (read-only) and give LAMS_Sales_Access Read FLS.
3. Create the email template, then the assignment rule with its three entries. Activate it.
4. Lead Settings: Default Lead Owner and notification.
5. Create the sharing rules and the list views.
6. Create and activate both matching rules. **Wait until they are Active**, then create the duplicate rule and the alert label (with Hindi draft: "इस PAN या मोबाइल वाली लीड या उधारकर्ता पहले से मौजूद है। मिलान देखें: यदि वही व्यक्ति है, तो इस लीड को Unqualified – Duplicate चिह्नित करें या मौजूदा उधारकर्ता में बदलें।"). The duplicate-rule alert field holds plain text, so paste the label's English value.
7. Add Potential Duplicates to the Lead record page.
8. By hand: create a lead as the admin with the mobile of demo borrower Aarav Sharma (`+919000000001`). Check the alert and save anyway; then delete the lead.
9. Write and run `LeadRoutingTest`: `sf apex run test --class-names LeadRoutingTest --result-format human --wait 10 --target-org Lams`.
10. Retrieve:
    `sf project retrieve start --metadata Queue:Leads_Retail Queue:Leads_Secured AssignmentRules:Lead EmailTemplate:LAMS_Internal_Templates/LAMS_Lead_Assigned CustomField:Lead.Product_Code__c CustomField:Lead.First_Contact_Overdue__c SharingRules:Lead ListView:Lead.LAMS_My_Open_Leads ListView:Lead.LAMS_Awaiting_First_Contact MatchingRules:Lead MatchingRules:Contact DuplicateRule:Lead.LAMS_Lead_Duplicate FlexiPage:LAMS_Lead_Record_Page CustomLabels Translations:hi --target-org Lams`
    `MatchingRules:Contact` brings back every Contact matching rule in one file, including LAMS-008's PAN rule. Deploy matching rules before the duplicate rule (activation is asynchronous).
11. Commit: `feat(sales): lead queues, assignment rule and duplicate rules [LAMS-096]`.

## Learn

- **Assignment rules:** one active rule per object, entries evaluated in order, first match wins. They run from the UI checkbox, from Web-to-Lead and from Apex or the API **only when asked**: `Database.DMLOptions.assignmentRuleHeader.useDefaultRule = true` (LAMS-097). A plain Apex `insert` leaves the owner as the running user.
- **Queues as owners:** queue members can view and take records from the queue. Converting a queue-owned lead needs a **user** owner for the new Account and Contact, which LAMS-098 handles.
- **Matching vs duplicate rules:** a matching rule says what counts as the same record, and can compare across objects with a field mapping (Lead → Contact). A duplicate rule says what happens. *Allow + Alert* warns in the UI, but in Apex the save **fails** with a `DuplicateError` unless `DuplicateRuleHeader.allowSave = true`.
- **Bypass sharing** in a duplicate rule lets the check see records the user can't open. The alert shows that a match exists, but it never opens the record to that user.

## Done when

- [ ] Queues Leads – Retail and Leads – Secured exist, with the LAMS_Sales_Access holder (Priya Sharma) as member
- [ ] **AC-17 (assignment part):** a Home Loan lead from Pune is owned by Leads – Secured; PL Mumbai goes to the named Loan Officer; anything else goes to Leads – Retail
- [ ] The new owner (or the queue members) receives the LAMS_Lead_Assigned email when the rule assigns a lead from the UI
- [ ] A lead still New more than one business day after creation appears in *Leads Awaiting First Contact* and drops out once Contacted
- [ ] A lead with the PAN or mobile of another lead or a borrower Contact shows the alert, can still be saved, and creates a Duplicate Record Set
- [ ] `LeadRoutingTest` passes, including the 200-lead insert
- [ ] Queues, rules, template, list views and sharing rules are in `force-app/`; the Default Lead Owner and the named-user entry are listed in the README as org-specific
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-84, BR-86; §9 AC-17; §11 Lead OWD Private, owner assignment; §13.6 Lead queues, Lead assignment rule, Lead duplicate rules; §21 Duplicate rules; §8 A5, C1; Appendix B B37
