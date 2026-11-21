# LAMS-065 · ClosureLetter PDF

**Milestone:** [M08 – Servicing](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-46

**Depends on:** LAMS-051 (LetterHeader, LetterFooter, LetterController, PDF-saving helper), LAMS-053 (LetterController loan branch and `letterLanguage`), LAMS-058 (loans reach Closed with Closure_Type__c)

## Goal

A closed loan gets a closure ("no dues") letter as a PDF on the loan record, in the borrower's language (BR-46). The Loan Event Handler (LAMS-066) generates and emails it when the *Loan Closed* event arrives. This item builds the page and proves it renders for both closure types.

## Build

**Visualforce page `ClosureLetter`** — `renderAs="pdf"`, `controller="LetterController"`, `language="{!letterLanguage}"`, `applyBodyTag="false"`, `standardStylesheets="false"`. Text comes from custom labels (proposed prefix `LAMS_Closure_`) with Hindi translations.

**LetterController additions** (closure branch):

| Property | Source |
| --- | --- |
| `loan` | `Loan__c` with Name, Borrower__r (Name, MailingAddress), Loan_Product__r.Name, Principal__c, Disbursement_Date__c, Tenure__c, Total_Paid__c, Closure_Type__c, Status__c |
| `closureDate` | MAX(`EMI_Instalment__c.Paid_Date__c`) for the loan (proposed; Loan__c has no closed-date field) |
| `isPrepaid` | `Closure_Type__c == 'Prepaid'` |
| `cancelledCount` | count of Cancelled instalments (shown for Prepaid) |

The controller throws a friendly error (label) if `Status__c` ≠ Closed, so a closure letter can never be produced for an open loan.

| Page section | Content |
| --- | --- |
| Header | `<c:LetterHeader>` |
| Reference | Letter date, loan number, borrower name and address |
| Body | "Loan {Name} for ₹{Principal__c} disbursed on {Disbursement_Date__c} has been closed on {closureDate}." Matured: "all {Tenure__c} instalments have been paid". Prepaid: "repaid early; {cancelledCount} future instalments cancelled" |
| Summary | Total paid (Total_Paid__c), outstanding ₹0, closure type |
| No-dues statement | "No amount is due on this loan." For a Home loan, add a line that the property papers can be collected (proposed) |
| Footer | `<c:LetterFooter>` |

**Generation:** call the LAMS-051 helper (proposed `LetterPdfService`) with `pageName` = `ClosureLetter`, `recordId` = loan Id, `fileName` = `Closure_Letter_{Loan.Name}.pdf`. The file is linked to the loan with `Visibility = AllUsers` so it appears on the portal's My Loans page. The Loan Event Handler (LAMS-066) calls this on Loan Closed and then sends `LAMS_Loan_Closed` through Send Notification.

## Steps

1. Add the closure branch to `LetterController` and the `LAMS_Closure_*` labels (EN/HI).
2. Create `pages/ClosureLetter.page`. Preview it with `/apex/ClosureLetter?id=<closedLoanId>` for a Matured loan and a Prepaid loan (use the LAMS-058 test scenarios in the org).
3. Generate the file from Anonymous Apex to prove the helper path works before LAMS-066 exists:
   `sf apex run --file scripts/apex/closure-letter-demo.apex` (proposed; calls the helper for one Closed loan).
4. Extend `LetterControllerTest`: Matured and Prepaid values, closureDate = last Paid_Date__c, Hindi language for a Hindi borrower, error for an Active loan.
5. `sf apex run test --class-names LetterControllerTest --code-coverage --result-format human --wait 10`
6. Retrieve: `sf project retrieve start --metadata ApexPage:ClosureLetter ApexClass:LetterController CustomLabels`
7. Commit: `feat(letters): ClosureLetter PDF [LAMS-065]`.

## Learn

- **One controller, three letters:** LetterController serves Offer, Agreement and Closure letters from the same header and footer components, so branding changes in one place.
- **The `language` attribute on `<apex:page>`** renders `$Label` values in that language for this page only, whatever the running user's language. A platform-event flow runs as the Automated Process user, so this is what makes Hindi letters possible.
- The Visualforce PDF engine needs a font that has the glyphs. For Hindi text, test `font-family: 'Arial Unicode MS'` early, because Devanagari may render without proper character joining.

## Done when

- [ ] `ClosureLetter` renders for a Matured loan and a Prepaid loan with the correct wording, closure date and total paid
- [ ] Requesting it for an Active loan shows an error, not a letter
- [ ] The generated `Closure_Letter_LN-xxxxxx.pdf` is attached to the loan and visible to the borrower in the portal (checked fully in M10)
- [ ] A Hindi-preference borrower's letter uses the Hindi labels
- [ ] LetterController tests pass with ≥ 90% coverage
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.7 BR-46, BR-54, §10.5 Closure_Type__c, Total_Paid__c, §13.2 Loan Event Handler (Loan Closed → ClosureLetter + email), §14 LetterController, §15 ClosureLetter, LetterHeader, LetterFooter
