# LAMS-076 · Portal pages and components

**Milestone:** [M10 – Portal](README.md) · **Size:** L (5–10h) · **Delivers:** BR-60

**Depends on:** LAMS-074 (site), LAMS-075 (theme layout), LAMS-034 (emiCalculator), LAMS-035 (New Loan Application flow), LAMS-045 (documentChecklist), LAMS-052 (Respond to Offer, Withdraw Application), LAMS-057 (emiSchedule, loanSummaryCard), LAMS-014 (Case record type Loan Service Request); LAMS-077 must follow before real borrowers use it

## Goal

Build the six portal pages of BR-60 so a borrower can apply, upload documents, accept or decline an offer, view loans and EMIs and raise service requests (BR-57, BR-60), reusing the LWCs and flows built for staff.

## Build

**Navigation menu** *LAMS Portal Menu* (proposed): Home · Apply · My Applications · My Loans · Service Requests · Assistant. Labels from custom labels (EN/HI).

**Pages and components**

| Page (URL) | Components (top to bottom) | Notes |
| --- | --- | --- |
| Home (`/`) | Rich Content Editor welcome text; `portalStatusBanner` slot (LAMS-079); **emiCalculator**; three tiles (Apply, My Applications, My Loans) | emiCalculator needs `lightningCommunity__Page` target |
| Apply (`/apply`) | **Flow** component → `New_Loan_Application` | Flow detects portal user (`$User.ContactId`) → Borrower = own Contact, Channel = Portal |
| My Applications – list (`/loan-application/Loan_Application__c/Default`) | Record List, list view *My Applications* (proposed): Name, Loan Product, Amount, Tenure, Status, Submitted Date, Offer Expiry Date | Object page for `Loan_Application__c` |
| My Applications – detail (`/loan-application/:recordId`) | Record Banner (Name, Status, Amount); Record Detail with layout *Loan Application – Portal* (proposed); **documentChecklist** (upload only for portal users); **Flow** `Respond_to_Offer` (visible when Status = Approved); **Flow** `Withdraw_Application` (visible when Status is Draft → Approved) | Component visibility uses record field conditions |
| My Loans – list (`/loan/Loan__c/Default`) | Record List, list view *My Loans* (proposed): Name, Principal, EMI Amount, Next Due Date, Outstanding Principal, Status | Object page for `Loan__c` |
| My Loans – detail (`/loan/:recordId`) | **loanSummaryCard**; **emiSchedule**; Related List *Payments* (Reference, Date, Amount, Mode, Status); Record Detail layout *Loan – Portal* (proposed) | Outstanding comes from loanSummaryCard |
| Service Requests (`/service-requests`) | Record List on Case, list view *My Service Requests* (proposed); **Create Case Form** using global action *New Service Request* (proposed) | Action fields: Loan__c, Request_Type__c, Subject, Description; record type Loan Service Request; Origin = Portal (predefined) |
| Case detail (standard) | Case Detail, Case Feed / comments | Borrower can add comments |
| Assistant (`/assistant`) | Placeholder text label `LAMS_Portal_Assistant_Coming` (proposed) | Borrower Assistant is embedded in LAMS-087 |
| Request a Callback (`/request-callback`), **built in LAMS-097** (M14), not in the menu | Rich-text intro; **callbackRequest** (guest EMI calculator and callback form) | The only page with Page Access *Public*; reached from a link on the Login page. Listed here so the page set is complete; nothing to build in this item |

**Portal page layouts** (assigned to profile LAMS Borrower) hide internal fields: Credit_Score__c, Credit_Score_Source__c, Override_Reason__c, Risk_Grade__c, Eligibility_Notes__c, Decision_Comments__c, AI_Summary__c, Assigned_Officer__c (proposed list). Field access itself is controlled by `LAMS_Borrower_Portal` FLS.

**Access checklist for `LAMS_Borrower_Portal` / profile LAMS Borrower**

| Item | Setting |
| --- | --- |
| Record types | Loan_Application__c: Personal, Home, Auto, Business; Case: Loan Service Request |
| Apex class access | Controllers used by emiCalculator, documentChecklist, emiSchedule, loanSummaryCard |
| Flow access | New_Loan_Application, Respond_to_Offer, Withdraw_Application |
| Objects | As BRD §11 (create/read own Application and Application Document; read Loan, EMI, Payment; create Case) |

**Files:** documents uploaded in the portal are ContentVersions linked to the Application_Document__c row; internal staff must see them (check *Visibility = AllUsers* on the link) so verification in LAMS-045 works.

## Steps

1. In Builder create the standard pages (Apply, Service Requests, Assistant) and object pages for Loan_Application__c, Loan__c and Case.
2. Create the list views (filter *All* — the sharing set in LAMS-077 limits rows) and portal page layouts; assign layouts to LAMS Borrower.
3. Create the global action *New Service Request* on Case with predefined Origin = Portal and record type Loan Service Request.
4. Place components as in the table; set component visibility on the application detail page.
5. Build the navigation menu; translate page text: Builder → Settings → Languages → export, add Hindi, import.
6. Publish: `sf community publish --name "LAMS Borrower Portal"`.
7. Log in as a portal borrower ("Log in to Experience as User" on their Contact) and run the journey: apply → upload → (staff approve) → accept → open loan → raise request.
8. Retrieve: `sf project retrieve start --metadata ExperienceBundle NavigationMenu Layout ListView QuickAction PermissionSet:LAMS_Borrower_Portal`
9. Record manual steps (publishing, translation import, component visibility if not retrieved) in the README.
10. Commit: `feat(portal): portal pages, menu and borrower layouts [LAMS-076]`.

## Learn

- **Object pages** (list, detail, related list) in Experience Builder are generated per object and reuse page layouts assigned to the portal profile.
- **LWC targets:** an LWC appears in Builder only with `lightningCommunity__Page` (and `lightningCommunity__Default` for design properties) in its `js-meta.xml`.
- **Component visibility** by record field avoids separate pages per status; it hides, it does not secure — validation and sharing still protect the data.
- Screen flows run in the portal as the portal user; anything they do must be allowed by that user's permissions and sharing.

## Done when

- [ ] All six menu pages exist in English and Hindi and use lamsPortalTheme
- [ ] As a portal borrower: an application can be created through Apply and appears in My Applications
- [ ] The borrower can upload a document on the application; a Loan Officer can see and verify it
- [ ] After approval the borrower can accept the offer; the loan then shows schedule, payments and outstanding in My Loans
- [ ] The borrower can raise a Statement request; it shows in My Service Requests with Origin = Portal
- [ ] No internal-only field (score, eligibility notes, AI summary) is visible to the borrower
- [ ] Site metadata in source; manual steps listed in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §15 components table and Portal paragraph, §13.2 New Loan Application, Respond to Offer, Withdraw Application, §10.8 Case, §11 `LAMS_Borrower_Portal`, §19 Not in source, BR-04, BR-17, BR-29, BR-32, BR-40, BR-57, BR-60, NFR-11, NFR-12
