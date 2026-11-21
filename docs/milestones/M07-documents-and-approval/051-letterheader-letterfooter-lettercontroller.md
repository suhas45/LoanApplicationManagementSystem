# LAMS-051 · LetterHeader, LetterFooter, LetterController, OfferLetter PDF

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** M (2–5h) · **Delivers:** BR-28

**Depends on:** LAMS-047 (Application_Decided flow, Approved branch), LAMS-048 / LAMS-049 (applications reach Approved), LAMS-021 (labels with Hindi)

## Goal

Approval issues an offer letter PDF valid for Offer_Validity_Days__c (BR-28), saved on the application where staff and the borrower can open it. The header, footer, controller and PDF helper built here are reused for the LoanAgreement (LAMS-053) and ClosureLetter (LAMS-065).

## Build

**Visualforce components**

| Component | Attributes | Renders |
| --- | --- | --- |
| `LetterHeader` | `title` (String, required), `reference` (String), `letterDate` (Date) | Logo from static resource `LAMS_Logo` (proposed), company name and address labels (`LAMS_Letter_Company_Name`, `LAMS_Letter_Company_Address`), title, reference, date |
| `LetterFooter` | `note` (String, optional) | Registration line label `LAMS_Letter_Footer`, optional note, "Page X of Y" — `position: running(footer)` with `@page { @bottom-center { content: element(footer); } }` and `counter(page)` / `counter(pages)` |

**Page `OfferLetter`** — `<apex:page controller="LetterController" renderAs="pdf" showHeader="false" sidebar="false" standardStylesheets="false" applyHtmlTag="false" applyBodyTag="false" language="{!languageCode}">`; inline CSS only; `font-family: 'Arial Unicode MS'` so Hindi text renders.

Content: `<c:LetterHeader>`; borrower name and mailing address; application Name and product; Approved_Amount__c, Interest_Rate__c, Tenure__c, EMI__c; processing fee amount and net disbursement; **valid until Offer_Expiry_Date__c**; how to accept or decline (portal or branch, BR-29); conditions; `<c:LetterFooter>`. All fixed text from labels.

**Class `LetterController`** — `public with sharing class` (it renders data the running user may see; generation runs as the user who caused the approval).

```apex
public LetterController();                      // reads ApexPages.currentPage().getParameters().get('id')
public Loan_Application__c application { get; private set; }
public Loan__c loan { get; private set; }        // used by LAMS-053 / LAMS-065
public Contact borrower { get; private set; }
public String languageCode { get; private set; } // 'hi' when Preferred_Language__c = Hindi, else 'en_US'
public Decimal processingFeeAmount { get; private set; }   // Approved_Amount × product Processing_Fee__c / 100
public Decimal netDisbursement { get; private set; }       // Approved_Amount − fee (BR-35)
public Date letterDate { get; private set; }
```

The Id's SObjectType decides what to load (Loan_Application__c now; Loan__c later). Missing or inaccessible Id → `ApexPages.addMessage` and an empty letter body, never an exception page.

**Class `LetterPdfService`** (proposed name, shared contract) — renders a VF page to PDF and saves it as a file on the record. `getContentAsPDF()` counts as a callout and is not allowed in trigger context, so it runs in a Queueable.

```apex
public without sharing class LetterPdfService implements Queueable, Database.AllowsCallouts {
    public class Request {
        @InvocableVariable(required=true) public Id recordId;
        @InvocableVariable(required=true) public String pageName;   // 'OfferLetter' | 'LoanAgreement' | 'ClosureLetter'
    }
    @InvocableMethod(label='Generate Letter PDF' category='LAMS')
    public static void generate(List<Request> requests);   // chunks of 50 → one job each
    public LetterPdfService(List<Request> requests);
    public void execute(QueueableContext ctx);
}
```

For each request: `PageReference pr = new PageReference('/apex/' + pageName); pr.getParameters().put('id', recordId);` → `Blob pdf = Test.isRunningTest() ? Blob.valueOf('PDF') : pr.getContentAsPDF();` (all renders first) → insert ContentVersion (Title `<label> – <record Name>`, PathOnClient `<pageName>-<Name>.pdf`) → insert ContentDocumentLink (LinkedEntityId = recordId, ShareType `V`, **Visibility `AllUsers`** so the borrower sees it in the portal). `pageName` is checked against an allow-list of the three pages.

**Flow change:** in `Application_Decided` (LAMS-047), Approved branch, add action *Generate Letter PDF* (pageName `OfferLetter`).

**Access:** grant Visualforce page access to OfferLetter in the staff permission sets (LAMS_Loan_Officer, LAMS_Credit, LAMS_Operations); borrowers read the generated file, not the page.

## Steps

1. Upload the logo as static resource `LAMS_Logo`; create the labels (with Hindi).
2. Create `LetterHeader` and `LetterFooter` (Developer Console or `force-app/main/default/components/*.component`), then `LetterController` and `OfferLetter`.
3. Preview `/apex/OfferLetter?id=<an approved application>` in English and Hindi.
4. `sf apex generate class --name LetterPdfService --output-dir force-app/main/default/classes`; tests `LetterControllerTest`, `LetterPdfServiceTest`.
5. Add the action to `Application_Decided`.
6. Retrieve and deploy: `sf project retrieve start --metadata ApexPage:OfferLetter ApexComponent:LetterHeader ApexComponent:LetterFooter StaticResource:LAMS_Logo Flow:Application_Decided`, then `sf project deploy start --source-dir force-app/main/default`.
7. `sf apex run test --class-names LetterControllerTest LetterPdfServiceTest --code-coverage --result-format human --wait 10`
8. Commit: `feat(vf): letter header/footer, LetterController and OfferLetter PDF [LAMS-051]`.

## Learn

- **`renderAs="pdf"`** uses a CSS 2.1 renderer: no JavaScript, no SLDS, limited CSS3; page headers and footers come from `@page` margin boxes and running elements.
- **Hindi in PDFs:** only fonts that ship with the renderer work — `Arial Unicode MS` covers Devanagari, but complex conjuncts may not shape perfectly; check with real text.
- **`getContentAsPDF()` is treated as a callout:** not in triggers, and no DML before it in the same transaction — render all, then insert all.
- **ContentVersion → ContentDocument → ContentDocumentLink:** the link (and its Visibility) is what attaches a file to a record and decides who sees it.

## Done when

- [ ] Approving an application (manual or auto) attaches *Offer Letter – LA-xxxxxx* PDF to it within a minute
- [ ] The PDF shows amount, rate, tenure, EMI, fee, net disbursement and the offer expiry date matching the record; header and footer with page numbers appear
- [ ] A Hindi-preference borrower gets the letter text in Hindi
- [ ] The portal borrower can open the PDF from their application (file visibility AllUsers)
- [ ] **AC-01** re-run: auto-approved ₹3 lakh Personal Loan has the offer email and the OfferLetter PDF
- [ ] `LetterControllerTest`: fee and net amounts, language code, missing Id handled; `LetterPdfServiceTest`: 200 requests → 4 jobs, a job creates one file and one AllUsers link per record, unknown page name rejected; coverage ≥ 90%
- [ ] Screenshot of the PDF in `docs/BRD/images/`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-28, BR-29, BR-35, BR-54, §10.3 Offer\_Expiry\_Date\_\_c, §13.4 final approval, §14 LetterController, §15 OfferLetter, LetterHeader, LetterFooter, AC-01
