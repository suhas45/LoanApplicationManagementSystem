# LAMS-097 · callbackRequest LWC + CallbackRequestController (portal guest) and Web-to-Lead form

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** L (5–10h) · **Delivers:** BR-83

**Depends on:** LAMS-098 (conversion, for the AC-17 end-to-end check), LAMS-095 (Lead fields, sources, `Lead_Enquiry_Defaults` flow, TestDataFactory lead helpers), LAMS-096 (assignment rule, duplicate rule, Default Lead Owner), LAMS-074 (LAMS Borrower Portal site and its guest user profile), LAMS-076 (portal pages and navigation), LAMS-079 (Portal_Enabled__c off behaviour), LAMS-034 (`calculateEmi` in emiCalculator), LAMS-017 / LAMS-019 / LAMS-020 (settings, FeatureToggle, post-deploy defaults), LAMS-021 (labels and Hindi)

## Goal

A visitor who is not logged in can ask for a callback from the EMI calculator on a public portal page. They enter product, amount, tenure, name, mobile, city and consent. The request becomes a New Lead with LeadSource *Portal Callback*, assigned by the lead rules (BR-83, BR-84). A standard Web-to-Lead enquiry form does the same for a public website with LeadSource *Website*. The guest path is narrow and safe: input is validated server-side, consent is required, each mobile number is rate-limited, and nothing is returned to the guest. This completes **AC-17** end to end with LAMS-096 and LAMS-098.

## Build

**Threshold (proposed): `LAMS_Settings__c.Callback_Rate_Limit__c`**: Number(2,0), default **3**, Org scope. It is the maximum number of Portal Callback leads per mobile in 24 hours. It already exists: it was created in LAMS-017, defaulted by the LAMS-020 script, read by `FeatureToggle.callbackRateLimit()` (Integer, LAMS-019) and shown on the lamsSettings screen (LAMS-030). Like every threshold getter, it throws `SettingsMissingException` when blank (LAMS-019). Thresholds are never hardcoded (NFR-09).

**Class `CallbackRequestController`**: `public without sharing class`. Add a class comment explaining why. Guest users have no read access to Lead (for the rate-limit count) or to Loan_Product__c (secure guest access forces Private), and they can't own records. Keep the class small: validate, check, insert, return nothing.

```apex
@AuraEnabled(cacheable=true)
public static List<ProductOption> getProducts();          // active products only
@AuraEnabled
public static void submit(CallbackRequest request);       // throws AuraHandledException with a label message

public class CallbackRequest {   // every member @AuraEnabled public … { get; set; }
    String firstName; String lastName; String businessName; String mobile; String email; String city;
    Id productId; Decimal amount; Integer tenure; Boolean consent;
}
public class ProductOption {      // public facts only
    Id id; String name; String code; Boolean isBusiness; Decimal interestRate;
    Decimal minAmount; Decimal maxAmount; Integer minTenure; Integer maxTenure;
}
@TestVisible static String normaliseMobile(String raw);    // '+91XXXXXXXXXX' or null
```

`getProducts`: `SELECT Id, Name, Product_Code__c, Record_Type_Name__c, Interest_Rate__c, Min_Amount__c, Max_Amount__c, Min_Tenure__c, Max_Tenure__c FROM Loan_Product__c WHERE Active__c = true ORDER BY Name`. `isBusiness` = `Record_Type_Name__c == 'Business'`. Eligibility fields (score, income, ratios) are never returned.

**`submit`**: checks in this order. Each failure throws `AuraHandledException` with the label, set through `setMessage(...)` so tests can read it.

| # | Check | Failure label |
| --- | --- | --- |
| 1 | `FeatureToggle.isPortalEnabled()` (BR-61) | `LAMS_Portal_Maintenance` (LAMS-021) |
| 2 | `consent == true` | `LAMS_Callback_Consent_Required` |
| 3 | lastName present, ≤ 80 characters; firstName ≤ 40; city present and matching `[\\p{L} .'-]{2,40}`; email blank or a valid address (≤ 80) | `LAMS_Callback_Invalid_Details` |
| 4 | `normaliseMobile`: strip spaces, `-`, `(` and `)`, then match `^(?:\\+?91\|0)?([6-9][0-9]{9})$` → `+91` + the 10 digits | `LAMS_Callback_Invalid_Mobile` |
| 5 | Product: `productId` is an active Loan_Product__c (one query) | `LAMS_Callback_Invalid_Product` |
| 6 | Amount and tenure within the product's Min/Max | `LAMS_VR_Amount_Out_Of_Range`, `LAMS_VR_Tenure_Out_Of_Range` (LAMS-021) |
| 7 | Business product → businessName required, ≤ 80 | `LAMS_Callback_Business_Name_Required` |
| 8 | Rate limit: `SELECT COUNT() FROM Lead WHERE MobilePhone = :mobile AND LeadSource = 'Portal Callback' AND CreatedDate >= :Datetime.now().addHours(-24)` must be below `FeatureToggle.callbackRateLimit()` | `LAMS_Callback_Too_Many` |
| 9 | Insert the Lead (fields below) with `Database.insert(lead, dmo)` | Any error → `System.debug(LoggingLevel.ERROR, …)` with the mobile masked to its last 4 digits, then `LAMS_Error_Generic`. Database messages never reach the guest |

| Lead field | Value |
| --- | --- |
| FirstName, LastName, Email, City | From the request, trimmed |
| MobilePhone | Normalised `+91…` |
| Company | Business: businessName. Individual: `firstName + ' ' + lastName` (Company is required, LAMS-095) |
| Borrower_Type__c | `Business` when the product is a business product, else `Individual` |
| Loan_Product__c, Requested_Amount__c, Requested_Tenure__c | From the request |
| Consent__c | true |
| LeadSource / Status | `Portal Callback` / `New` |
| Preferred_Language__c | `Hindi` when `UserInfo.getLanguage()` starts with `hi` (the site language the visitor picked), else `English` |

```apex
Database.DMLOptions dmo = new Database.DMLOptions();
dmo.assignmentRuleHeader.useDefaultRule = true;   // LAMS Lead Assignment (LAMS-096); guests can't own records
dmo.EmailHeader.triggerUserEmail = true;          // assignment email to the new owner
dmo.DuplicateRuleHeader.allowSave = true;         // LAMS_Lead_Duplicate alerts, but the lead must still be saved
```

**LWC `callbackRequest`** (`force-app/main/default/lwc/callbackRequest/`): targets `lightningCommunity__Page`, `lightningCommunity__Default`

| Part | Spec |
| --- | --- |
| Data | `@wire(getProducts)` fills a `lightning-combobox` |
| Inputs | Amount and tenure (`lightning-input` type number, min and max from the chosen product); first name; last name (required); business name (shown and required only for a business product); mobile (`type="tel"`); city (required); email (optional); consent checkbox with the full consent text as its label |
| EMI | Shows the indicative EMI with the shared `calculateEmi(amount, product.interestRate, tenure)` from LAMS-034. Import it the way LAMS-057 does. This makes the form an EMI calculator with a callback button (BR-83 "from the EMI calculator") |
| Submit | `reportValidity()` on every input first; Submit stays disabled until consent is ticked. Call `submit` imperatively; while waiting, show a spinner and disable the button (no double posts) |
| Result | Success: hide the form and show `LAMS_Callback_Success`. Error: show the returned message in a `div role="alert" aria-live="assertive"` |
| Text | Every label, placeholder and message is a custom label (EN/HI, NFR-12). Every input has a visible label (NFR-11) |
| Jest `__tests__/callbackRequest.test.js` | Renders products from a wire mock; Submit disabled without consent; EMI shown for a valid amount and tenure; business-name field appears only for a business product; `submit` called with the entered values; success hides the form; a rejected call shows the error text |

**Portal changes** (LAMS Borrower Portal; these change LAMS-074's "public access off")

| Setting | Value |
| --- | --- |
| Builder → Settings → General → *Public can access the site* | **On**. Afterwards check that every existing page is still *Requires Login* |
| New page *Request a Callback* (`/request-callback`, proposed) | Page Access **Public**. Components: rich-text intro (label), `callbackRequest`. Uses lamsPortalTheme |
| Login page | A link "Request a callback instead" (label `LAMS_Callback_Link`) to `/request-callback` (proposed) |
| Guest user profile *LAMS Borrower Portal Profile* | Apex Class Access: add `CallbackRequestController` (next to BorrowerSelfRegController). **No** object permissions |
| Optional (Parking lot) | Pre-fill from the emiCalculator on Home through Lightning Message Service. It needs a change to LAMS-034, so it is not in this item |

**Web-to-Lead enquiry form**

| Item | Value |
| --- | --- |
| New Lead field `Web_Product_Code__c` (proposed) | Text(2). Web-to-Lead can only post plain values. A product lookup would need record Ids in a public HTML file. Read FLS on LAMS_Sales_Access |
| `Lead_Enquiry_Defaults` flow (LAMS-095) | Add a **first** step: when Web_Product_Code__c is set and Loan_Product__c is blank → Get Records Loan_Product__c by Product_Code__c (active) → set Loan_Product__c, and set Borrower_Type__c = Business when its Record_Type_Name__c = Business. The existing Company step then fills an individual's name over `[not provided]` |
| Validation rule `Lead_Consent_Required` (new) | `AND(ISNEW(), OR(ISPICKVAL(LeadSource, "Website"), ISPICKVAL(LeadSource, "Portal Callback")), NOT(Consent__c))`. Label LAMS_Callback_Consent_Required. A web post without consent is not stored |
| Setup → Web-to-Lead | Enabled. Default Lead Creator = the admin user (active; the Credit Head role in `Lams`). Default Response Template: **none** (proposed; saves the 15-a-day email allowance) |
| Form (Setup → Web-to-Lead → Create Web-to-Lead Form) | Fields: First Name, Last Name, Company (shown as "Business name – Small-Business Loan only"), Mobile, Email, City, Web Product Code (edit the HTML into a `<select>` with PL, HL, AL, BL and product names), Requested Amount, Requested Tenure, Consent. Hidden: `lead_source` = `Website`. Return URL: a thank-you page (proposed `thank-you.html` next to the form) |
| HTML edits | Add `required` to last name, mobile, city and consent; `pattern="[6-9][0-9]{9}"` with a hint on mobile; `min`/`max` hints on amount and tenure |
| File | `web/enquiry-form.html` and `web/thank-you.html` (proposed). Host them on GitHub Pages, or open the file locally for the demo. The generated HTML contains the org Id and the custom-field Ids (`00N…`), so regenerate it for another org |
| reCAPTCHA (recommended) | Register a reCAPTCHA v2 key pair for the hosting domain, add it in Setup → Web-to-Lead → *Require reCAPTCHA Verification*, and regenerate the form with *Include reCAPTCHA in HTML*. Without it, bots can fill the lead queue |

Web-to-Lead runs the active assignment rule and the duplicate rule (Allow), so web leads are routed and flagged the same way as callbacks. The callback LWC and Web-to-Lead don't share the rate limit; reCAPTCHA is the web form's protection. Portal_Enabled__c doesn't switch the web form off, because it isn't part of the portal.

**Custom labels** (category `LAMS Portal`; Hindi drafts for review, D4)

| Label | English | Hindi (draft) |
| --- | --- | --- |
| LAMS_Callback_Title | Request a callback | कॉलबैक का अनुरोध करें |
| LAMS_Callback_Intro | Tell us what you need. A loan officer will call you within one business day. | हमें बताएं आपको क्या चाहिए। एक ऋण अधिकारी एक कार्य दिवस के भीतर आपको कॉल करेगा। |
| LAMS_Callback_Product / _Amount / _Tenure / _First_Name / _Last_Name / _Business_Name / _Mobile / _City / _Email | Loan product / Loan amount (₹) / Tenure (months) / First name / Last name / Business name / Mobile number / City / Email (optional) | ऋण उत्पाद / ऋण राशि (₹) / अवधि (महीने) / पहला नाम / उपनाम / व्यवसाय का नाम / मोबाइल नंबर / शहर / ईमेल (वैकल्पिक) |
| LAMS_Callback_Emi | Indicative EMI | अनुमानित ईएमआई |
| LAMS_Callback_Consent | I agree that LAMS may call me and use these details to respond to my loan enquiry. | मैं सहमत हूँ कि LAMS मुझे कॉल कर सकता है और मेरी ऋण पूछताछ का उत्तर देने के लिए इन विवरणों का उपयोग कर सकता है। |
| LAMS_Callback_Submit | Request callback | कॉलबैक का अनुरोध भेजें |
| LAMS_Callback_Success | Thank you. A loan officer will call you within one business day. | धन्यवाद। एक ऋण अधिकारी एक कार्य दिवस के भीतर आपको कॉल करेगा। |
| LAMS_Callback_Consent_Required | Please give your consent so that we can call you. | कृपया अपनी सहमति दें ताकि हम आपको कॉल कर सकें। |
| LAMS_Callback_Invalid_Details | Please check your name, city and email. | कृपया अपना नाम, शहर और ईमेल जांचें। |
| LAMS_Callback_Invalid_Mobile | Enter a 10-digit Indian mobile number. | 10 अंकों का भारतीय मोबाइल नंबर दर्ज करें। |
| LAMS_Callback_Invalid_Product | Please choose a loan product. | कृपया एक ऋण उत्पाद चुनें। |
| LAMS_Callback_Business_Name_Required | Enter the business name for a Small-Business Loan. | लघु व्यवसाय ऋण के लिए व्यवसाय का नाम दर्ज करें। |
| LAMS_Callback_Too_Many | We have already received your request. A loan officer will call you soon. | हमें आपका अनुरोध पहले ही मिल चुका है। एक ऋण अधिकारी जल्द ही आपको कॉल करेगा। |
| LAMS_Callback_Link | Request a callback instead | इसके बजाय कॉलबैक का अनुरोध करें |

**Tests `CallbackRequestControllerTest`.** Most tests run as the site's guest user: `[SELECT Id FROM User WHERE UserType = 'Guest' AND Profile.Name = 'LAMS Borrower Portal Profile' LIMIT 1]`. User rows are visible in tests, and running as the guest proves the class access. Insert LAMS_Settings__c org defaults (Portal_Enabled__c true, Callback_Rate_Limit__c 3) and products before `runAs`; assert as the admin afterwards.

| Test | Assert |
| --- | --- |
| `ac17_homeLoanCallbackFromPune` | HL, ₹40,00,000, 240 months, city Pune, consent → one Lead: LeadSource Portal Callback, Status New, Company = full name, Borrower Type Individual, mobile `+91…`, Consent true, **owner = queue Leads_Secured** |
| `businessCallbackUsesBusinessName` | BL with businessName → Company = business name, Borrower Type Business; without businessName → `LAMS_Callback_Business_Name_Required` |
| `consentRequired` | consent false → `LAMS_Callback_Consent_Required`; no Lead |
| `invalidInputRefused` | Bad mobile, missing last name, digits in city, bad email, inactive product, unknown Id, amount and tenure out of range → each its label; no Lead |
| `rateLimitPerMobile` | 3 earlier Portal Callback leads for the mobile (via `insertLeads`) → 4th refused with `LAMS_Callback_Too_Many`; another mobile still works; a lead older than 24 h (`Test.setCreatedDate`) doesn't count |
| `rateLimitIgnoresOtherMobiles` (bulk) | 200 Portal Callback leads for other mobiles → the request is accepted |
| `portalOffRefused` / `portalOnAccepted` | Portal_Enabled__c false → `LAMS_Portal_Maintenance`; true → Lead created |
| `duplicateStillSaved` | Mobile of an existing borrower Contact → Lead saved (allowSave) |
| `getProductsReturnsActiveOnly` | Inactive product not returned |
| `normaliseMobileVariants` | `98765 43210`, `+91-98765-43210`, `09876543210` → `+919876543210`; `12345` → null |
| `webLeadDefaults` (Website path, no guest) | Insert a Lead as Web-to-Lead would: LeadSource Website, Company `[not provided]`, Web_Product_Code__c `HL`, consent → Loan_Product__c = HL, Company = full name; without consent → `Lead_Consent_Required` |

## Steps

1. Check that Callback_Rate_Limit__c = 3 on the org default (LAMS-017 / LAMS-020). If the org was built before the field existed, re-run `sf apex run --file scripts/apex/set-lams-settings-defaults.apex --target-org Lams`; it fills blank thresholds only.
2. Create the labels with Hindi; create `Web_Product_Code__c`, the consent rule and the new flow step.
3. `sf apex generate class --name CallbackRequestController --output-dir force-app/main/default/classes` (and the test); `sf lightning generate component --type lwc --name callbackRequest --output-dir force-app/main/default/lwc`.
4. Write the controller, LWC and tests; `npm run test:unit -- callbackRequest`; deploy with `sf project deploy start --source-dir force-app/main/default --target-org Lams`.
5. Run `sf apex run test --class-names CallbackRequestControllerTest --code-coverage --result-format human --wait 10 --target-org Lams`.
6. In Experience Builder: turn on public access, create *Request a Callback* (Public), add the component and the Login link. Give the guest profile the Apex class. Publish: `sf community publish --name "LAMS Borrower Portal" --target-org Lams`.
7. **AC-17 by hand.** Open `/request-callback` in a private window (no login). Request a Home Loan, ₹40,00,000, 240 months, city Pune. As the admin, see the Lead in the Leads – Secured queue. As Priya Sharma, take it, mark it Contacted and then Qualified (add PAN), and *Convert to Application* (LAMS-098). Check: an Individual Borrower Account and Contact, a Draft Home application for ₹40,00,000 and 240 months, no opportunity. Use one demo lead only: each assignment email uses the daily allowance.
8. Enable Web-to-Lead, generate the form, edit it into `web/enquiry-form.html`, and submit one Personal Loan enquiry. Check the Lead (Website, product resolved, Company = full name, Mumbai → Priya). Optionally add reCAPTCHA.
9. Retrieve: `sf project retrieve start --metadata ApexClass:CallbackRequestController ApexClass:CallbackRequestControllerTest LightningComponentBundle:callbackRequest CustomField:Lead.Web_Product_Code__c ValidationRule:Lead.Lead_Consent_Required Flow:Lead_Enquiry_Defaults ExperienceBundle "Profile:LAMS Borrower Portal Profile" CustomLabels Translations:hi --target-org Lams` (check the real ExperienceBundle and guest profile names with `sf org list metadata`).
10. Record in the README: public access on, Request a Callback page, Web-to-Lead settings, reCAPTCHA keys (never committed), and where the form is hosted.
11. Commit: `feat(sales): guest callback request LWC and Web-to-Lead enquiry form [LAMS-097]`.

## Learn

- **Guest user security:**
  - Secure guest access makes every object Private for the guest.
  - The guest can't own records or update existing ones.
  - Each Apex class must be granted to the guest profile.
  - A `without sharing` controller is the doorway, so it must validate everything, write one record and return nothing a stranger shouldn't see.
- **Running assignment rules from Apex:** `Database.DMLOptions` with `assignmentRuleHeader.useDefaultRule` (and `EmailHeader.triggerUserEmail` for the notification). Without it, an Apex insert keeps the running user as the owner, and for a guest that fails.
- **Web-to-Lead:**
  - Up to 500 leads a day; extra requests are queued, and the Default Lead Creator is emailed.
  - Custom fields are posted by field Id, so the form is org-specific.
  - A submission that fails a validation rule is not saved.
  - reCAPTCHA is the built-in bot protection.
  - Assignment and duplicate rules run as for any new lead.
- **`AuraHandledException`** hides server details from the browser. Call `setMessage()` as well as passing the message to the constructor, or Apex tests read "Script-thrown exception" instead of your label.

## Done when

- [ ] **AC-17 end to end:** a guest's portal callback for a ₹40 lakh Home Loan from Pune creates a New Lead (Portal Callback) owned by Leads – Secured. Converting it creates an Individual Borrower Account + Contact and a Draft Home application for ₹40,00,000 with the requested tenure, and no opportunity
- [ ] Consent missing, invalid input, out-of-range amount or tenure, and a 4th request from one mobile within 24 hours are each refused with their label, and no Lead is created; the limit comes from Callback_Rate_Limit__c
- [ ] With Portal_Enabled__c off the request is refused with the maintenance label; on, it works
- [ ] The guest profile has Apex access to CallbackRequestController and no object permissions; all other portal pages still require login
- [ ] The Web-to-Lead form creates a Website lead with its product resolved, Company = full name for an individual, consent required, assigned by the rule
- [ ] `CallbackRequestControllerTest` passes with ≥ 90% coverage; Jest tests for callbackRequest pass
- [ ] All callback text is in English and Hindi labels
- [ ] Source committed; manual site and Web-to-Lead steps in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-83, BR-84, BR-86; §9 AC-17; §10.12 Lead (Consent__c, LeadSource values); §12 Portal_Enabled__c and "How toggles are read"; §13.6 callbackRequest and Web-to-Lead form; §14 CallbackRequestController; §15 Portal; BR-54, BR-61; NFR-09, NFR-11, NFR-12
