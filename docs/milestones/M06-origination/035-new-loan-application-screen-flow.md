# LAMS-035 · New Loan Application screen flow

**Milestone:** [M06 – Origination](README.md) · **Size:** L (5–10h) · **Delivers:** BR-01, BR-04

**Depends on:** LAMS-034 (emiCalculator), LAMS-009 (Loan_Application__c fields and record types), LAMS-015 (record pages, LAMS app), LAMS-024 (permission sets), LAMS-027 (FLS: borrowers cannot edit Status__c), LAMS-031 (amount/tenure validation rules), LAMS-094 and LAMS-008 (Individual Borrower and Business Borrower record types, PAN duplicate rule, for the new-borrower path)

## Goal

A Loan Officer (Lightning) or a Borrower (portal) captures an application for one product, sees the EMI live, and either saves a Draft to resume later or submits it (BR-01, BR-04). Product-specific details are asked only for the product that needs them (BR-05).

## Build

**Flow `New_Loan_Application`** — label *New Loan Application*, type Screen Flow, **How to Run the Flow = System Context With Sharing – Enforces Record-Level Access**. Borrowers have no field-level edit on Status__c (LAMS-027), so the flow writes Status in system mode; record-level sharing still applies, so a borrower can only resume a Draft they can see (their own, through the sharing set). The flow writes only the fields its screens show.

**Variables**

| Name | Type | In/Out | Use |
| --- | --- | --- | --- |
| `recordId` | Text | Input | Id of a Draft application to resume (from the *Resume Application* quick action); blank for a new one |
| `applicationId` | Text | Output | Id of the saved record (portal page redirects to it) |
| `varApplication` | Record (Loan_Application__c) | – | Record being built |
| `varProduct` | Record (Loan_Product__c) | – | Chosen product |
| `varIsPortalUser` | Formula (Boolean) | – | `NOT(ISBLANK({!$User.ContactId}))` |

**Elements in order**

| # | Element | Details |
| --- | --- | --- |
| 1 | Decision *Resume?* | `recordId` not blank → Get Records Loan_Application__c (Id = recordId, Status = Draft); not found → error screen (label `LAMS_App_Not_Draft`) |
| 2 | Screen *Product* | Radio buttons from a Record Choice Set on Loan_Product__c, filter `Active__c = true`, label Name, value Id. Skipped on resume (product is kept) |
| 3 | Get Records *Product* | Loan_Product__c by chosen Id → `varProduct` |
| 4 | Get Records *Record type* | RecordType where `SobjectType = 'Loan_Application__c'` and `DeveloperName = {!varProduct.Record_Type_Name__c}` (no hardcoded Ids, NFR-09) |
| 5 | Decision *Who is applying?* | `varIsPortalUser` → Borrower = `{!$User.ContactId}` Channel = Portal. Otherwise → screen *Borrower* (5a–5c), Channel = Branch |
| 5a | Screen *Borrower* (staff) | Radio *Existing borrower* / *New borrower* (proposed). Existing → Lookup component on Borrower__c (Contact): it finds both individual borrowers and Small-Business directors, because both are Contacts. For BL pick the director Contact of a Business Borrower Account (§10.1) |
| 5b | New individual (proposed; PL, HL, AL) | Screen with First Name, Last Name, Birthdate, Mobile, Email, PAN, Employment Type, Monthly Income, Existing EMI, Preferred Language → **Create Records Account** with RecordTypeId = Individual Borrower (Get Records on RecordType by DeveloperName `Individual_Borrower`), Name = `{!FirstName} {!LastName}` → **Create Records Contact** with AccountId = the new Account, FirstName, LastName, Birthdate, MobilePhone, Email, PAN__c, Employment_Type__c, Monthly_Income__c, Existing_EMI__c, Preferred_Language__c → Borrower = new Contact Id |
| 5c | New business (proposed; BL) | Screen with business name and the director's details → Create Records Account (RecordTypeId = Business Borrower, Name) → Create Records Contact (AccountId = new Account, director fields with `__c` names) → Borrower = new Contact Id |
| 6 | Screen *Loan details* | `c:emiCalculator` with rate = `varProduct.Interest_Rate__c`, min/max amount and tenure from `varProduct`; amount and tenure mapped back to `varApplication`. Purpose__c (long text). Conditional visibility by `varProduct.Product_Code__c`: HL → Property_Value__c; AL → Vehicle_Price__c, Dealer_Name__c; BL → GST_Number__c, Annual_Turnover__c (BR-05) |
| 7 | Screen *Review* | Display text summary (product, amount, tenure, EMI) + radio choice *Save as draft* / *Submit now* |
| 8 | Create or Update Records | Loan_Application__c: Borrower__c, Loan_Product__c, RecordTypeId, Amount__c, Tenure__c, Purpose__c, product fields, Channel__c, **Status__c = Draft**, Last_Activity_Date__c = `{!$Flow.CurrentDateTime}` |
| 9 | Decision *Submit now?* | Yes → Update Records Status__c = Submitted. A second update (after the Draft save) keeps the BR-08 lock rule from seeing amount and status change together (proposed) |
| 10 | Screen *Done* | Label `LAMS_App_Saved_Draft` or `LAMS_App_Submitted`, with the application Name |

**Fault paths:** every Create/Update has a fault connector to one *Error* screen showing `{!$Flow.FaultMessage}` (validation messages from LAMS-031 appear here, e.g. amount outside product limits; a new borrower with an existing PAN shows the duplicate-rule alert from LAMS-008).

**Campaign (v2.2):** when LAMS-099 adds `Loan_Application__c.Campaign__c`, add it as an optional field on the staff *Borrower* screen and to element 8, because §10.12 lets the officer choose the campaign. Applications created by lead conversion (LAMS-098) get it from the lead.

**Text:** every screen label, help text and message is a custom label referenced as `{!$Label.LAMS_...}` (proposed names prefixed `LAMS_App_`).

**Where it is launched**

| Place | How |
| --- | --- |
| Lightning | LAMS app page *Apply* (or Home) with the Flow component; quick action *Resume Application* on Loan_Application__c (passes `recordId`), shown only when Status = Draft (Dynamic Actions) |
| Portal | *Apply* page (wired in LAMS-076) |

The flow only saves Draft or sets Submitted; everything that happens on submission is in the Application Submitted flow (LAMS-038).

## Steps

1. Build the flow in Flow Builder in the element order above; create the labels first so screens can reference them.
2. Create the *Resume Application* quick action on Loan_Application__c and add it to the record pages with a visibility filter Status = Draft.
3. Add the flow to an *Apply* Lightning page in the LAMS app.
4. Debug as a Loan Officer (Run as another user in Flow debug) for each of PL, HL, AL, BL.
5. Retrieve: `sf project retrieve start --metadata Flow:New_Loan_Application QuickAction:Loan_Application__c.Resume_Application FlexiPage CustomLabels`.
6. Commit: `feat(flow): New Loan Application screen flow [LAMS-035]`.

## Learn

- **Record Choice Sets** build choices from a query, so a fifth product needs no flow change.
- **Record type from data:** looking up RecordType by DeveloperName keeps Ids out of the flow and works in every org. The same applies to the Account record types Individual Borrower and Business Borrower.
- **One Account per borrower:** a new individual gets their own Individual Borrower Account and one Contact. Create the Contact second, after the Account, so its AccountId is known; if the Contact fails (for example a duplicate PAN), the fault rolls back the whole interview, including the Account.
- **Conditional visibility** on screen components replaces separate screens per product.
- **Run modes:** *System Context With Sharing* skips object and field permissions but keeps record sharing — the right choice when users may change a field (Status) only through this guided path, never by editing the record.
- Screen flows cannot be unit-tested in Apex; test them by debugging as each user, and keep logic that needs tests in Apex or record-triggered flows.

## Done when

- [ ] A Loan Officer creates a Personal Loan Draft, closes the flow, resumes it via *Resume Application* and submits it; Status ends Submitted (then Document Review once LAMS-038 is in)
- [ ] Record type matches the product (Home Loan → Home) for all four products
- [ ] Home shows Property Value only; Auto shows Vehicle Price and Dealer; Business shows GST Number and Turnover; Personal shows none
- [ ] Amount outside the product limits shows the validation message on the Error screen and saves nothing
- [ ] EMI updates live while typing the amount (LAMS-034 inside the flow)
- [ ] Channel = Branch for staff; Portal and Borrower = own Contact when run by a portal user (checked again in LAMS-076)
- [ ] A Loan Officer can pick an existing borrower (Aarav Sharma) and the director Kavya Iyer for BL; a new individual creates one Individual Borrower Account and one Contact, and that Contact becomes Borrower__c; a new individual with an existing PAN is stopped with the duplicate message
- [ ] A portal borrower can submit through the flow, but editing Status__c on the record directly is not possible (no FLS edit)
- [ ] Resume with another borrower's application Id finds nothing (record-level sharing enforced)
- [ ] No hardcoded Ids or literal text in the flow (labels only)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-01, BR-02, BR-03, BR-04, BR-05, BR-08, §10.1 borrower Accounts and Contacts, §10.12 Campaign__c, §10.2 Record\_Type\_Name\_\_c, §10.3, §13.2 New Loan Application, §15 emiCalculator and portal Apply page, NFR-09
