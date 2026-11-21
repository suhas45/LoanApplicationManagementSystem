# LAMS-095 · Lead fields, statuses and sources, conversion field mapping, Path with guidance

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** M (2–5h) · **Delivers:** BR-85, BR-87, §10.12

**Depends on:** M10 done; LAMS-094 (Account record types, one Account per borrower), LAMS-007 (Loan_Product__c), LAMS-008 (Contact borrower fields, the mapping targets), LAMS-015 (LAMS app), LAMS-021 (label convention and Hindi routine), LAMS-024 (`LAMS_Sales_Access`: Lead object access, Convert Leads, Campaign read), LAMS-026 (Lead OWD Private), LAMS-029 (Priya Sharma, Loan Officer 1, the only user holding LAMS_Sales_Access), LAMS-033 (TestDataFactory)

## Goal

The standard Lead holds a loan enquiry: product of interest, amount, tenure, borrower details and consent (BR-83). It moves New → Contacted → Qualified → Converted, or ends Unqualified with a reason, and a Path shows guidance and key fields at each stage (BR-85). On conversion the borrower fields land on the new Contact (BR-87). First_Contacted_At__c is stamped for the time-to-first-contact report (BR-89, LAMS-100). Person Accounts are not used (LAMS-094), so **Company is always filled in**: an individual's full name, or the business name. Borrower_Type__c (proposed) records which of the two the lead is.

## Build

**Lead custom fields** (Object Manager → Lead)

| Field (API name) | Type | Details |
| --- | --- | --- |
| Loan_Product__c | Lookup(Loan_Product__c) | Product of interest. Lookup filter `Loan_Product__c.Active__c = true` (proposed, required filter). Child relationship `Leads`. On product delete: clear the value |
| Requested_Amount__c | Currency(16,2) | |
| Requested_Tenure__c | Number(3,0) | Months |
| PAN__c | Text(10) | **Not** unique and not an External ID: duplicates are flagged, not blocked (BR-86, LAMS-096). Maps to Contact.PAN__c |
| Employment_Type__c | Picklist (restricted) | Salaried, Self-Employed, Business (same values as Contact, LAMS-008). Maps to Contact |
| Monthly_Income__c | Currency(16,2) | Maps to Contact |
| Preferred_Language__c | Picklist (restricted) | English (default), Hindi. Maps to Contact |
| Consent__c | Checkbox | Default false. Required for callback and web leads (LAMS-097) |
| Unqualified_Reason__c | Picklist (restricted) | Not Interested, Not Eligible, Unreachable, Duplicate, Other |
| First_Contacted_At__c | Date/Time | Stamped by the *Lead Contacted Stamp* flow; read-only for everyone |
| Borrower_Type__c | Picklist (restricted), **proposed** | Individual (default), Business. Decides the Account record type on conversion (LAMS-098): Individual → `Individual_Borrower`, Business → `Business_Borrower` |

Standard fields used: FirstName, LastName, **Company** (required on Lead without Person Accounts), MobilePhone, Email, City, LeadSource, Status, Description, Owner. Add inline help to Company: "Individual: the person's full name. Business: the registered business name." Picklist value API names equal their labels (LAMS-008 rule).

**Lead Status** (Setup → Object Manager → Lead → Fields → Lead Status; standard value set `LeadStatus`)

| Value | Default | Converted | Meaning |
| --- | --- | --- | --- |
| New | Yes | | Not yet called |
| Contacted | | | First call made |
| Qualified | | | Loan details complete; ready to convert |
| Unqualified | | | Closed with Unqualified_Reason__c |
| Converted | | **Yes** | The only converted value; set by conversion |

Delete the standard values (Open - Not Contacted, Working - Contacted, Closed - Converted, Closed - Not Converted). If sample leads still use them, choose *New* as the replacement.

**Lead Source** (standard value set `LeadSource`, shared with Contact and Opportunity): Website, Portal Callback, Branch Walk-in, Partner Referral, Campaign. Remove or deactivate the other standard values (Web, Phone Inquiry, Purchased List, Other).

**Validation rules on Lead.** The message text is the label's English value. A rule can't reference `$Label`; see LAMS-021.

| Rule | Formula | Label |
| --- | --- | --- |
| `Lead_PAN_Format` | `AND(NOT(ISBLANK(PAN__c)), NOT(REGEX(PAN__c, "[A-Z]{5}[0-9]{4}[A-Z]")))` | LAMS_VR_Lead_PAN_Format |
| `Lead_Mobile_Format` | `AND(NOT(ISBLANK(MobilePhone)), NOT(REGEX(MobilePhone, "\\+91[6-9][0-9]{9}")))`. One stored format makes the duplicate match in LAMS-096 work; the defaults flow normalises the number first | LAMS_VR_Lead_Mobile_Format |
| `Lead_Unqualified_Reason_Required` | `AND(ISPICKVAL(Status, "Unqualified"), ISBLANK(TEXT(Unqualified_Reason__c)))` | LAMS_VR_Lead_Unqualified_Reason |
| `Lead_Qualified_Needs_Details` | `AND(ISPICKVAL(Status, "Qualified"), OR(ISBLANK(Loan_Product__c), ISBLANK(Requested_Amount__c), ISBLANK(Requested_Tenure__c), ISBLANK(PAN__c), ISBLANK(MobilePhone)))`. BR-87 needs product, amount and tenure; PAN finds an existing borrower (LAMS-098) | LAMS_VR_Lead_Qualified_Details |
| `Lead_Amount_In_Product_Range` (proposed) | `AND(ISPICKVAL(Status, "Qualified"), OR(Requested_Amount__c < Loan_Product__r.Min_Amount__c, Requested_Amount__c > Loan_Product__r.Max_Amount__c))` | LAMS_VR_Amount_Out_Of_Range (existing, LAMS-021) |
| `Lead_Tenure_In_Product_Range` (proposed) | Same with Requested_Tenure__c and Min/Max_Tenure__c | LAMS_VR_Tenure_Out_Of_Range (existing) |
| `Lead_Borrower_Type_Matches_Product` (proposed) | `AND(ISPICKVAL(Status, "Qualified"), NOT(ISBLANK(Loan_Product__c)), OR(AND(Loan_Product__r.Record_Type_Name__c = "Business", NOT(ISPICKVAL(Borrower_Type__c, "Business"))), AND(Loan_Product__r.Record_Type_Name__c <> "Business", ISPICKVAL(Borrower_Type__c, "Business"))))` | LAMS_VR_Lead_Borrower_Type |

The product-range and borrower-type rules check only at **Qualified**. A Website lead with an odd amount must still save, because a Web-to-Lead record that fails validation is not created (LAMS-097).

**Custom labels** (category `LAMS Validation`; Hindi drafts need a native speaker's review, D4)

| Label | English | Hindi (draft) |
| --- | --- | --- |
| LAMS_VR_Lead_PAN_Format | PAN must be 10 characters: 5 capital letters, 4 digits, 1 capital letter (for example ABCDE1234F). | PAN 10 अक्षरों का होना चाहिए: 5 बड़े अक्षर, 4 अंक, 1 बड़ा अक्षर (उदाहरण ABCDE1234F)। |
| LAMS_VR_Lead_Mobile_Format | Enter the mobile number as +91 followed by 10 digits, for example +919876543210. | मोबाइल नंबर +91 के बाद 10 अंकों में दर्ज करें, उदाहरण +919876543210। |
| LAMS_VR_Lead_Unqualified_Reason | Select a reason when marking a lead Unqualified. | लीड को Unqualified चिह्नित करते समय कारण चुनें। |
| LAMS_VR_Lead_Qualified_Details | Enter the loan product, amount, tenure, PAN and mobile before marking the lead Qualified. | लीड को Qualified चिह्नित करने से पहले ऋण उत्पाद, राशि, अवधि, PAN और मोबाइल दर्ज करें। |
| LAMS_VR_Lead_Borrower_Type | Borrower type must be Business for a Small-Business Loan and Individual for every other product. | लघु व्यवसाय ऋण के लिए उधारकर्ता प्रकार Business और अन्य सभी उत्पादों के लिए Individual होना चाहिए। |

**Flows on Lead**

| Flow (API name) | Trigger | Logic |
| --- | --- | --- |
| `Lead_Enquiry_Defaults` (proposed) | Record-triggered, before save (*Fast Field Updates*), created or updated, no entry condition | 1. **Company:** when `Borrower_Type__c` = Individual and Company is blank or `[not provided]` (what Web-to-Lead writes when the form has no company), set Company = `TRIM({!$Record.FirstName} & " " & {!$Record.LastName})`. 2. **Mobile:** formula strips spaces, `-`, `(` and `)`. A 10-digit result becomes `+91` + digits; `91` + 10 digits becomes `+` + digits; anything else is left alone, so `Lead_Mobile_Format` reports it. LAMS-097 adds a third step (web product code) |
| `Lead_Contacted_Stamp` | Record-triggered, before save, created or updated. Condition (formula): `AND(NOT(ISPICKVAL({!$Record.Status}, "New")), ISBLANK({!$Record.First_Contacted_At__c}))` | Assignment: First_Contacted_At__c = `{!$Flow.CurrentDateTime}`. The BRD says "the first time Status = Contacted". Firing on the **first status after New** (proposed) also stamps a lead that an officer moves straight to Qualified or Unqualified, so time to first contact is never missing |

Because the blank check is part of the condition, the stamp is set once and never moves. For API and Apex saves, Salesforce checks required fields again **after** before-save flows, so the defaults flow can fill Company for an Apex-created individual lead. The standard UI still asks for Company on the form.

**Lead field mapping** (Object Manager → Lead → Fields & Relationships → *Map Lead Fields*; metadata `LeadConvertSettings`)

| Lead field | → Contact field | Notes |
| --- | --- | --- |
| PAN__c | PAN__c | Unique on Contact (LAMS-008). LAMS-098 reuses an existing Contact with the same PAN instead of creating a second one |
| Employment_Type__c | Employment_Type__c | Same picklist values on both |
| Monthly_Income__c | Monthly_Income__c | |
| Preferred_Language__c | Preferred_Language__c | Picks the email language later (BR-54) |
| FirstName, LastName, MobilePhone, Email, City, LeadSource | Standard mapping (Contact name, MobilePhone, Email, MailingCity, LeadSource) | Built in; nothing to set. Company → Account Name |

**Not mapped (by design):** Loan_Product__c, Requested_Amount__c, Requested_Tenure__c, Consent__c, Unqualified_Reason__c, First_Contacted_At__c, Borrower_Type__c. Lead mapping can only target Account, Contact and Opportunity fields. The product, amount and tenure go onto Loan_Application__c in Apex (LAMS-098), which reads them from the converted Lead.

**Lead Settings** (Setup → Lead Settings; metadata `LeadConfigSettings`, retrieved as `Settings:LeadConfig`)

| Setting | Value | Why |
| --- | --- | --- |
| Hide Opportunity section of Convert Lead window | On | No opportunity is ever created (BR-87, C4) |
| Select "Don't create an opportunity upon conversion" by default | On | Same, in case the section shows |
| Require Validation for Converted Leads | **On** | Validation rules **and Lead triggers** run during conversion. LAMS-098's LeadTrigger depends on it |
| Default Lead Owner | Set in LAMS-096 (queue Leads – Retail) | Until then, leave the admin |

**Path** (Setup → Path Settings → Enable; then New Path). Name `LAMS_Lead_Path`, label *LAMS Lead Path*, object Lead, record type Master, picklist Status. Celebration: off.

| Step | Key fields | Guidance for success (rich text, proposed wording) |
| --- | --- | --- |
| New | MobilePhone, City, Loan_Product__c, Requested_Amount__c, Owner | Call within **one business day** (BR-84). Confirm the customer asked for a callback and gave consent. After three failed attempts, mark the lead Unqualified with reason *Unreachable*. |
| Contacted | Requested_Tenure__c, Employment_Type__c, Monthly_Income__c, Preferred_Language__c | Confirm the product, amount and tenure. Ask about employment and monthly income, and explain which documents the product needs. |
| Qualified | Borrower_Type__c, Company, PAN__c, Requested_Amount__c, Requested_Tenure__c | Check the PAN. For an individual, Borrower Type = Individual and Company = the customer's full name. For a Small-Business Loan, Borrower Type = Business and Company = the business name; the lead becomes the director. Then use **Convert to Application** (LAMS-098). |
| Unqualified | Unqualified_Reason__c, Description | Choose the reason and add a short note in Description. *Duplicate* means another lead or borrower is the same person (LAMS-096). |
| Converted | – | A borrower Account, its Contact and a Draft application now exist. Open the application from the Contact's Loan Applications list to complete it. |

Path guidance can't use custom labels. Its Hindi text, if wanted, goes in Translation Workbench (*Path Step Rich Text*). Staff work in English (LAMS-029), so this is optional.

**Layout and page**

| Item | Spec |
| --- | --- |
| Page layout *LAMS Lead Layout* (proposed), assigned to all profiles | Enquiry (Name, Company, Borrower Type, MobilePhone, Email, City, Lead Source, Status, Lead Owner, Consent); Loan Interest (Loan Product, Requested Amount, Requested Tenure); Borrower (PAN, Employment Type, Monthly Income, Preferred Language); Follow-up (First Contacted At, Unqualified Reason, Description). Related lists: Campaign History, Activity History, Open Activities |
| Lightning page `LAMS_Lead_Record_Page` (proposed), Header and Right Sidebar | Highlights panel; **Path**; Details; Related; sidebar: Activity. Activate as org default for Lead in the LAMS app |
| LAMS app | Add the **Leads** navigation item after Loan Applications |

**Field-level security** goes on **`LAMS_Sales_Access`** only (BRD v2.3, D6). That set already has Lead object access and Convert Leads from LAMS-024, and it is assigned directly, never through a group, to full-licence users. In `Lams` that is Priya Sharma. A Salesforce Platform user can't hold Lead permissions, so no Lead access goes into LAMS_Loan_Officer, LAMS_Credit or LAMS_Operations.

| Permission set | Lead fields |
| --- | --- |
| LAMS_Sales_Access | Edit: Loan_Product__c, Requested_Amount__c, Requested_Tenure__c, PAN__c, Employment_Type__c, Monthly_Income__c, Preferred_Language__c, Consent__c, Unqualified_Reason__c, Borrower_Type__c. Read: First_Contacted_At__c |

The admin, acting as Credit Head, sees every Lead field as System Administrator, so the sales reports (LAMS-100) need no extra set.

**Tests `LeadSetupTest`** (proposed name; record-triggered flows and validation rules run inside Apex tests). Add these to **TestDataFactory**:

| Method | Returns |
| --- | --- |
| `newLead(Loan_Product__c p, Integer i)` | Lead, not inserted: LastName `Lead` + i, FirstName `Test`, Company = full name, Borrower_Type__c Individual (Business when `p.Record_Type_Name__c = 'Business'`, with Company `Test Business ` + i), MobilePhone `+9198` + i padded to 8 digits, PAN `LEADP` + i padded to 4 digits + `Z`, City Mumbai, Status New, LeadSource Branch Walk-in, Consent__c true, amount and tenure = the product minimums. Unique PAN and mobile per i keep the LAMS-096 duplicate rule quiet |
| `insertLeads(List<Lead> leads, Boolean runAssignment)` | Inserts with `Database.DMLOptions`: `DuplicateRuleHeader.allowSave = true`, and `assignmentRuleHeader.useDefaultRule = runAssignment` |
| `loanOfficer()` | The existing active user with a direct `LAMS_Sales_Access` assignment (Priya Sharma): `SELECT AssigneeId FROM PermissionSetAssignment WHERE PermissionSet.Name = 'LAMS_Sales_Access' AND Assignee.IsActive = true LIMIT 1`. The org has only two full Salesforce licences, so a test that inserts a new Salesforce-licence user can fail with `LICENSE_LIMIT_EXCEEDED` |

| Test | Assert |
| --- | --- |
| `stampOnFirstStatusChange` | New → Contacted sets First_Contacted_At__c; a later change to Qualified leaves it unchanged |
| `stampWhenSkippingContacted` | New → Unqualified (with reason) sets the stamp |
| `companyDefaultsToFullName` | Individual lead inserted from Apex with Company blank, and one with `[not provided]` → Company = "Test Lead1" |
| `mobileNormalised` | `98765 43210` and `919876543210` → `+919876543210`; `12345` → fails `Lead_Mobile_Format` |
| one `_fails` / `_passes` pair per validation rule | Error message equals the `System.Label` value |
| `bulk200` | 200 leads inserted and moved to Contacted in one update → 200 stamps, no limit errors |
| `loanOfficerCanEditLeadFields` | `System.runAs(TestDataFactory.loanOfficer())`: insert and update a lead using every editable field |

## Steps

1. Create the fields, then the Status and Lead Source values.
2. Create the labels (with Hindi), then the seven validation rules.
3. Build and activate `Lead_Enquiry_Defaults` and `Lead_Contacted_Stamp`.
4. Map the lead fields and set Lead Settings.
5. Enable Path and build `LAMS_Lead_Path`; build the layout and the record page; add Leads to the LAMS app.
6. Add the FLS above to LAMS_Sales_Access.
7. By hand, as Priya Sharma (Loan Officer): create a lead, move it through Contacted and Qualified, and check the Path guidance and the stamp. Then click the standard **Convert** to check the mapping: the new Contact has PAN__c, Employment_Type__c, Monthly_Income__c and Preferred_Language__c, the Account is named after Company, and the convert window shows no opportunity section. (Without LAMS-098 no application is created yet. Delete the test Account afterwards: storage is 5 MB.)
8. Write the TestDataFactory methods and `LeadSetupTest`; run `sf apex run test --class-names LeadSetupTest --result-format human --wait 10 --target-org Lams`.
9. Retrieve:
   `sf project retrieve start --metadata CustomObject:Lead StandardValueSet:LeadStatus StandardValueSet:LeadSource LeadConvertSettings Settings:LeadConfig PathAssistant:LAMS_Lead_Path Flow:Lead_Enquiry_Defaults Flow:Lead_Contacted_Stamp "Layout:Lead-LAMS Lead Layout" FlexiPage:LAMS_Lead_Record_Page CustomApplication:LAMS CustomLabels Translations:hi PermissionSet:LAMS_Sales_Access --target-org Lams`
   (Path Settings itself is an org setting; if `PathAssistantSettings` doesn't come back, list it as a manual step in the README.)
10. Commit: `feat(sales): Lead fields, statuses, conversion mapping and Path [LAMS-095]`.

## Learn

- **Converted status:** exactly one Lead Status value is flagged *Converted*. The convert window offers only converted values, and Apex reads it with `SELECT MasterLabel FROM LeadStatus WHERE IsConverted = true`, never a literal.
- **Lead field mapping** copies lead fields onto the new Account, Contact or Opportunity only, between fields of a compatible type. Custom objects such as Loan_Application__c can't be targets, so those values are copied in Apex.
- **Company is required on Lead** unless Person Accounts are enabled. Conversion turns Company into the Account Name. That is why individual leads carry the person's full name there, and why Web-to-Lead writes `[not provided]` when the form has no company field.
- **Path** is a presentation layer on a picklist: steps follow the picklist order, guidance and key fields are per step, and one path is defined per record type.

## Done when

- [ ] Lead has the 11 custom fields; Status has exactly New, Contacted, Qualified, Unqualified, Converted (only Converted is converted); Lead Source has the 5 values
- [ ] Unqualified without a reason, Qualified without product, amount, tenure, PAN or mobile, and Qualified with an out-of-range amount or the wrong Borrower Type are each blocked with their label text
- [ ] First_Contacted_At__c is stamped on the first status after New and never changes afterwards
- [ ] An individual lead saved from Apex with no Company gets the full name; `98765 43210` is stored as `+919876543210`
- [ ] Converting a test lead with the standard Convert button copies PAN, employment, income and language onto the new Contact, names the Account after Company, and offers no opportunity
- [ ] Require Validation for Converted Leads is on
- [ ] The Lead page shows the Path with the guidance and key fields above; Leads is in the LAMS app
- [ ] Priya Sharma (LAMS_Sales_Access) can edit the Lead fields; no Lead permission or Lead FLS is in LAMS_Loan_Officer, LAMS_Credit or LAMS_Operations
- [ ] `LeadSetupTest` passes (validation rules and flows have no coverage figure; the tests guard behaviour)
- [ ] Metadata in `force-app/`; manual steps (Path Settings if not retrieved) in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-83, BR-85, BR-87, BR-89; §10.12 Lead fields, Status and LeadSource values; §10.1 Borrower (superseded by LAMS-094: no Person Accounts); §11 Lead OWD; Appendix D6 (LAMS_Sales_Access); §13.6 Lead Path, Lead Contacted Stamp; §14 LeadConversionService; Appendix C (C3, C4)
