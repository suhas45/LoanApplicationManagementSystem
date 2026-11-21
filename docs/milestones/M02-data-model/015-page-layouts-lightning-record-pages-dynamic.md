# LAMS-015 · Page layouts, Lightning record pages (Dynamic Forms), LAMS app, tabs

**Milestone:** [M02 – Data model](README.md) · **Size:** L (5–10h) · **Delivers:** BR-05

**Depends on:** LAMS-008 – LAMS-014 (every object and field it lays out); LAMS-094 (Account record types Individual Borrower and Business Borrower)

## Goal

Staff work in one Lightning app, *LAMS*, and each application record type shows only its own product details: property value for Home, vehicle price and dealer for Auto, GST number and turnover for Business (BR-05). Sections appear only when they mean something for the current status.

## Build

**Page layouts**

| Object | Layout name | Assigned to | Sections (in order) | Related lists |
| --- | --- | --- | --- | --- |
| Loan_Application__c | Loan Application - Personal / - Home / - Auto / - Business | Matching record type (System Administrator now; LAMS profiles in LAMS-023) | Application (Name, Borrower, Loan Product, Status, Channel, Partner Name, External Reference); Loan Request (Amount, Tenure, Purpose, Interest Rate, EMI); **Product Details** (Home: Property Value, LTV; Auto: Vehicle Price, Dealer Name, LTV; Business: GST Number, Annual Turnover; Personal: none); Credit and Eligibility (Credit Score, Credit Score Source, Override Reason, Risk Grade, EMI To Income, Eligibility Result, Eligibility Notes, Eligibility Run Date); Documents (Mandatory Docs, Mandatory Docs Verified, Docs Complete); Field Verification (Home and Business only: Field Verification Status); Decision (Approved Amount, Rejection Reason, Decision Comments, Decision Date, Offer Expiry Date, Offer Accepted Date, Withdrawal Reason); System (Submitted Date, Last Activity Date, AI Summary, Created By, Last Modified By) | Documents, Loans, Cases, Approval History, Files, Activity History |
| Loan__c | Loan Layout | All | Loan (Name, Loan Application, Borrower, Loan Product, Status, Closure Type, Assigned Officer); Terms (Principal, Interest Rate, Tenure, EMI Amount, Processing Fee Amount, Net Disbursement); Disbursement (Disbursement Status, Date, Reference, Payout Account, Core Banking Sync Status); Repayment (Total Paid, Principal Repaid, Outstanding Principal, Overdue Amount, Next Due Date, Days Past Due, Overdue Bucket) | EMI Schedule, Payments, Cases, Open Activities, Activity History |
| Case | Loan Service Request Layout | Record type Loan_Service_Request | Request (Request Type *required*, Loan, Loan Application, Prepayment Quote Amount, Contact, Origin, Status, Priority); Description (Subject, Description) | Activity History, Files |
| Contact | Borrower Layout (proposed) | Master record type (every borrower Contact: the individual, or the Small-Business director) | Contact standard fields (Account Name = the borrower's own Account); Borrower (PAN *required on layout*, Birthdate, Employment Type, Monthly Income, Existing EMI, Preferred Language); KYC (KYC Status, KYC Verified Date); Insights (Repayment Score, Pre Approved) | Loan Applications, Loans, Cases |
| Account | Individual Borrower Layout (proposed) | Account record type Individual Borrower | Account Name (= the borrower's full name), Phone, Billing Address, Owner. The borrower details live on the Contact | Contacts (the one borrower Contact), Cases, Activity History |
| Account | Business Borrower Layout (proposed) | Account record type Business Borrower | Account Name, Phone, Website, Billing Address, Industry, Owner | Contacts (directors), Cases, Activity History |
| Application_Document__c, EMI_Instalment__c, Payment__c, Integration_Log__c, Loan_Product__c | Default layouts, tidied (proposed) | All | All fields, system fields last | Files (documents), Document Checklist (product) |

Make Status__c, Interest_Rate__c, Credit_Score__c, Eligibility_Result__c, Eligibility_Run_Date__c, Submitted_Date__c, Offer_Expiry_Date__c and Last_Activity_Date__c **read-only on the application layouts** (proposed): automation sets them.

**Compact layouts (highlights panel, proposed)**

| Object | Name | Fields |
| --- | --- | --- |
| Loan_Application__c | `LAMS_Application_Compact` | Name, Borrower, Status, Amount, EMI, Risk Grade |
| Loan__c | `LAMS_Loan_Compact` | Name, Borrower, Status, Outstanding Principal, Next Due Date, Overdue Bucket |

**Lightning record pages with Dynamic Forms**

| FlexiPage (API name, proposed) | Object | Template | Content |
| --- | --- | --- | --- |
| `Loan_Application_Personal` / `_Home` / `_Auto` / `_Business` | Loan_Application__c | Header and Right Sidebar | Highlights panel; *Details* tab with Field Sections migrated from the matching layout (*Upgrade Now*); *Related* tab; sidebar: Activity. emiCalculator and documentChecklist are added later (LAMS-034, LAMS-045) |
| `Loan_Record_Page` | Loan__c | Header and Right Sidebar | Highlights panel, record detail, related lists. emiSchedule and loanSummaryCard come in LAMS-057 |
| `Individual_Borrower_Record_Page` (proposed) | Account | Header and Right Sidebar | Highlights panel; record detail; Contacts related list (the borrower, one click to their applications and loans); sidebar: Activity |
| `Business_Borrower_Record_Page` (proposed) | Account | Header and Right Sidebar | Highlights panel; record detail; Contacts (directors) related list; sidebar: Activity |

Visibility rules on the application pages (proposed):

| Section or field | Visible when |
| --- | --- |
| Credit and Eligibility section | Status ≠ Draft |
| Override Reason field | Credit Score Source = Manual Override |
| Decision section | Status is Approved, Rejected, Offer Accepted, Offer Declined, Withdrawn or Expired |
| Withdrawal Reason field | Status = Withdrawn |
| Field Verification section (Home, Business pages only) | Status ≠ Draft |

Activation: *App, Record Type and Profile* → app LAMS, each page to its record type (the two borrower pages to the Account record types Individual Borrower and Business Borrower), profile System Administrator (LAMS-023 adds LAMS Internal User).

**Lightning app**

| Setting | Value |
| --- | --- |
| Developer name / label | `LAMS` / LAMS |
| Navigation, form factor | Standard navigation; Desktop and Phone |
| Navigation items (in order) | Loan Applications, Loans, Loan Products, Cases, Integration Logs, Reports, Dashboards, plus Accounts and Contacts (proposed: officers look up borrowers; each borrower is a Contact under an Individual Borrower or Business Borrower Account) |
| Utility bar | Left empty; the EMI calculator item is added in LAMS-034 |
| Branding | Primary colour `#0B5CAB` (proposed); no logo needed |
| User profiles | System Administrator now; LAMS profiles in LAMS-023 |

**Tabs:** Loan_Product__c (LAMS-007), Loan_Application__c (LAMS-009), Loan__c (LAMS-012) and Integration_Log__c (LAMS-014) should already exist; create any that are missing, choosing any tab style.

## Steps

1. Build the four application layouts (clone the default layout once per record type), then assign them in *Page Layout Assignment*.
2. Build the Loan, Case, Contact and tidied default layouts, and the two compact layouts (set each as the object's primary compact layout). Build the Individual Borrower and Business Borrower layouts under Object Manager → **Account** → Page Layouts, then assign each to its Account record type.
3. In Lightning App Builder create `Loan_Application_Personal`, run *Upgrade Now* to migrate the layout's fields into Field Sections, add the visibility rules, save and activate. Clone it for Home, Auto and Business and adjust the Product Details section.
4. Create `Loan_Record_Page` and the two borrower pages, and activate them.
5. Create the LAMS app in App Manager.
6. Retrieve (quote names with spaces):
   `sf project retrieve start --metadata "Layout:Loan_Application__c-Loan Application - Personal" "Layout:Loan_Application__c-Loan Application - Home" "Layout:Loan_Application__c-Loan Application - Auto" "Layout:Loan_Application__c-Loan Application - Business" "Layout:Loan__c-Loan Layout" "Layout:Case-Loan Service Request Layout" "Layout:Contact-Borrower Layout" "Layout:Account-Individual Borrower Layout" "Layout:Account-Business Borrower Layout" CompactLayout:Loan_Application__c.LAMS_Application_Compact CompactLayout:Loan__c.LAMS_Loan_Compact FlexiPage:Loan_Application_Personal FlexiPage:Loan_Application_Home FlexiPage:Loan_Application_Auto FlexiPage:Loan_Application_Business FlexiPage:Loan_Record_Page FlexiPage:Individual_Borrower_Record_Page FlexiPage:Business_Borrower_Record_Page CustomApplication:LAMS`
   Retrieve the tidied default layouts the same way.
7. Check: one application per record type shows the right sections.
8. Screenshot one Home and one Auto application page for `docs/BRD/images/`.
9. Commit: `feat(ui): layouts, Dynamic Forms record pages and LAMS app [LAMS-015]`.

## Learn

- **Dynamic Forms** moves fields from the page layout onto the Lightning page, with per-section and per-field visibility rules. The page layout still controls related lists (unless you use Dynamic Related Lists), quick actions and mobile layouts.
- **Where assignments live:** Lightning page activation by app, record type and profile is stored in the `CustomApplication` metadata, so retrieve the app after activating. Page layout assignments are stored on the **Profile**, so they deploy only once profiles are in source (LAMS-023).
- **Layout read-only vs field-level security:** read-only on a layout is a UI convenience; it does not stop Apex, flows or the API. Real restrictions come from FLS (LAMS-027) and validation rules (M05).
- Visibility rules hide a section on the page; they do not secure the data, and hidden required fields still block a save if they are required on the layout.
- **Record types pick layouts and pages:** the two Account record types share one object but get their own layout and Lightning page. The applications and loans hang off the borrower Contact (Borrower__c), so they show on the Contact page, not the Account page.

## Done when

- [ ] A Home application shows Property Value and LTV and no vehicle or GST fields; an Auto one shows Vehicle Price, Dealer Name and LTV; a Business one shows GST Number and Annual Turnover; a Personal one shows none of them (BR-05)
- [ ] On a Draft application the Credit and Eligibility and Decision sections are hidden; setting Status to Rejected shows the Decision section
- [ ] The LAMS app shows the navigation items in the stated order
- [ ] The highlights panels show the compact-layout fields
- [ ] An Individual Borrower Account shows its one borrower Contact; a Business Borrower Account shows its director in the Contacts related list; the borrower Contact page shows the Borrower, KYC and Insights sections and the Loan Applications related list
- [ ] All layouts, compact layouts, FlexiPages and the app are in source and `sf project deploy start --dry-run --source-dir force-app` succeeds
- [ ] Screenshots saved in `docs/BRD/images/`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §15 UI (Application record pages, Page layouts, LAMS app); §10.1 borrower record types; §10.3 product-specific fields; §21 Page layouts, Lightning pages, Dynamic Forms; Apps, tabs, utility bar; BR-04, BR-05
