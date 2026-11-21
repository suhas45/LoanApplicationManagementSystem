# LAMS-053 · Offer Accepted flow + LoanAgreement PDF

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-29, BR-33

**Depends on:** LAMS-012 (Loan__c, Application_Key__c), LAMS-037 (OwnerAssignmentService picks the Operations Officer), LAMS-051 (LetterHeader, LetterFooter, LetterController, PDF-saving helper), LAMS-052 (Respond to Offer sets Status = Offer Accepted)

## Goal

When the borrower accepts the offer, exactly one loan is created in Pending Disbursement, assigned to an Operations Officer, and a loan agreement PDF is saved on it (BR-29, BR-33). The disbursement and sharing items (LAMS-054, LAMS-056) start from this record.

## Build

**Flow `Offer_Accepted`** (label *Offer Accepted*), record-triggered, after save, on `Loan_Application__c`.

| Setting | Value |
| --- | --- |
| Trigger | A record is created or updated |
| Entry condition | `Status__c` = *Offer Accepted* |
| When to run | Only when a record is updated to meet the condition requirements |
| Optimize for | Actions and Related Records |
| Run asynchronously path | Yes, for the PDF (see step 6) |

Elements, in order:

1. **Get Records** `Loan__c` where `Application_Key__c` = `{!$Record.Id}`. If found, stop. This guard makes a re-run harmless; the unique field is the backstop.
2. **Get Records** `Loan_Product__c` = `{!$Record.Loan_Product__c}` (for `Processing_Fee__c`).
3. **Apex action** OwnerAssignmentService (LAMS-037) in its Operations Officer mode. It returns the active Operations Officer with the fewest loans not Closed (BR-33).
4. **Formula** `principal` = `BLANKVALUE({!$Record.Approved_Amount__c}, {!$Record.Amount__c})`. Use the fallback because the auto-approve path may not set Approved_Amount__c.
5. **Create Records** `Loan__c`:

| Field | Value |
| --- | --- |
| Loan_Application__c | `{!$Record.Id}` |
| Application_Key__c | `{!$Record.Id}` (18-character Id; enforces one loan per application) |
| Borrower__c | `{!$Record.Borrower__c}` |
| Loan_Product__c | `{!$Record.Loan_Product__c}` |
| Principal__c | `principal` |
| Interest_Rate__c | `{!$Record.Interest_Rate__c}` (fixed at submission, BR-09) |
| Tenure__c | `{!$Record.Tenure__c}` |
| EMI_Amount__c | `{!$Record.EMI__c}` (EmiScheduleService rewrites it rounded to ₹1 in LAMS-055) |
| Processing_Fee_Amount__c | `ROUND(principal * Processing_Fee__c / 100, 0)` (proposed rounding to ₹1) |
| Status__c | Pending Disbursement |
| Disbursement_Status__c | Pending |
| Assigned_Officer__c | User Id from step 3 |
| OwnerId | `{!$Record.OwnerId}`, the Loan Officer (proposed). A portal borrower must never own the loan, and role hierarchy then opens it to the Credit Manager and Credit Head |

   Net_Disbursement__c is a formula (Principal − fee, BR-35), so do not set it.

6. **Run Asynchronously path:** call the LAMS-051 PDF helper (proposed name `LetterPdfService`, inputs `pageName` = `LoanAgreement`, `recordId` = new Loan Id, `fileName` = `Loan_Agreement_{Loan.Name}.pdf`). The helper renders the page with `getContentAsPDF()`, inserts a `ContentVersion` and links it to the loan with `ContentDocumentLink.Visibility = AllUsers` so the borrower sees it in the portal. To get the loan Id there, do another Get Records by `Application_Key__c`.
7. **Fault paths** on steps 3, 5 and 6: create a Task for the application owner (Subject from custom label `LAMS_Task_Loan_Creation_Failed`, proposed) and save the fault message.

**Visualforce page `LoanAgreement`** — `renderAs="pdf"`, `controller="LetterController"` (extend the LAMS-051 controller with a loan branch: it reads `Loan__c` with `Borrower__r`, `Loan_Product__r`, `Loan_Application__r`), `language="{!letterLanguage}"`. Set `letterLanguage` to `hi` when `Borrower__r.Preferred_Language__c` = Hindi, otherwise `en_US`. Text comes from custom labels (proposed prefix `LAMS_Agreement_`).

| Page section | Content |
| --- | --- |
| Header | `<c:LetterHeader>` (logo, lender address, date) |
| 1. Parties | Borrower name, address, PAN masked to last 4; lender |
| 2. Loan terms | Loan number (Name), product, Principal__c, Interest_Rate__c (fixed, A2), Tenure__c, EMI_Amount__c |
| 3. Fees and payout | Processing_Fee_Amount__c, Net_Disbursement__c paid to the borrower's account (dealer's for Auto) |
| 4. Repayment | EMIs fall on the disbursement day of each month, day 28 if later (BR-37); oldest dues paid first (BR-42) |
| 5. Late payment | Product Late_Fee__c % per month on the unpaid EMI after Grace_Days__c days (BR-48) |
| 6. Prepayment | Payoff quote on request; full payment closes the loan (BR-44) |
| 7. Acceptance | "Accepted electronically on {Offer_Accepted_Date__c}"; signature blocks |
| Footer | `<c:LetterFooter>` (page x of y, registered office) |

## Steps

1. Extend `LetterController` with the loan branch and the `letterLanguage` property. Add the `LAMS_Agreement_*` labels and their Hindi translations.
2. Create `pages/LoanAgreement.page`. Preview it at `/apex/LoanAgreement?id=<loanId>` against a hand-made loan.
3. Build `Offer_Accepted` in Flow Builder as specified above. Debug it on an Approved test application: set its Status to Offer Accepted, then roll back.
4. Extend `LetterControllerTest`: loan branch fields, Hindi vs English language, and a test that the flow creates one loan (update an application to Offer Accepted inside `Test.startTest()`/`stopTest()`).
5. Retrieve: `sf project retrieve start --metadata Flow:Offer_Accepted ApexPage:LoanAgreement ApexClass:LetterController ApexClass:LetterControllerTest CustomLabels`
6. Run tests: `sf apex run test --class-names LetterControllerTest --code-coverage --result-format human --wait 10`
7. Commit: `feat(servicing): Offer Accepted flow and LoanAgreement PDF [LAMS-053]`.

## Learn

- **Async path in record-triggered flows:** `PageReference.getContent()`/`getContentAsPDF()` is not allowed in trigger context. The *Run Asynchronously* path runs after commit in its own transaction, where it is allowed.
- **One-to-one with a unique text field:** a lookup cannot be unique, so `Application_Key__c` (Unique) blocks a second loan even if two transactions race past the Get Records guard.
- **Files and portal users:** a file linked with `Visibility = InternalUsers` is invisible in Experience Cloud even when the borrower can read the record. Set `AllUsers` on the `ContentDocumentLink`.
- In tests `getContentAsPDF()` does not render. The helper should use `Test.isRunningTest() ? Blob.valueOf('pdf') : page.getContentAsPDF()`.

## Done when

- [ ] Setting an Approved application to Offer Accepted creates exactly one Loan__c with Status Pending Disbursement, Disbursement_Status Pending, Application_Key__c = application Id and all copied fields as in the table
- [ ] Processing_Fee_Amount__c = Principal × product fee and Net_Disbursement__c = Principal − fee (₹3,00,000 PL → fee ₹6,000, net ₹2,94,000)
- [ ] Assigned_Officer__c is the Operations Officer with the fewest loans not Closed; OwnerId is the application owner, never a portal user
- [ ] Updating the application again (or re-running the flow) creates no second loan; inserting a duplicate Application_Key__c by hand fails
- [ ] `Loan_Agreement_LN-xxxxxx.pdf` is attached to the loan, opens with all 7 sections, and shows Hindi text for a Hindi-preference borrower
- [ ] Tests for the LetterController loan branch pass with ≥ 90% coverage
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.5 BR-29, §6.6 BR-33, BR-35, §10.5 Loan__c, §13.2 Offer Accepted, §14 OwnerAssignmentService and LetterController, §15 LoanAgreement, LetterHeader, LetterFooter, BR-54
