# LAMS-021 · Custom labels (first set) + Hindi translations

**Milestone:** [M03 – Configuration](README.md) · **Size:** M (2–5h) · **Delivers:** BR-54

**Depends on:** LAMS-005 (Translation Workbench on, Hindi active)

## Goal

All user-facing text is a custom label with a Hindi translation, never a literal in code (BR-54, NFR-09, NFR-12). This item creates the first set: validation messages for M05, settings screen text for LAMS-030 and shared errors. It also sets up the routine for translating labels and keeping the translations in source. Later items add their own labels the same way.

## Build

**Naming convention (proposed):** `LAMS_<Area>_<Meaning>`. The areas are `VR` (validation rule), `Settings`, `Error` and `Portal`. Set Category to the area (`LAMS Validation`, `LAMS Settings`, `LAMS Error`, `LAMS Portal`). Short Description = the name in words. Language = English, Protected = false.

**Validation messages** (used by LAMS-031/032, asserted by LAMS-033):

| Label name | English value | Hindi value (draft) | Rule (BR) |
| --- | --- | --- | --- |
| LAMS_VR_Amount_Out_Of_Range | Amount must be within the product's minimum and maximum amount. | राशि उत्पाद की न्यूनतम और अधिकतम सीमा के भीतर होनी चाहिए। | BR-03 |
| LAMS_VR_Tenure_Out_Of_Range | Tenure must be within the product's minimum and maximum months. | अवधि उत्पाद की न्यूनतम और अधिकतम महीनों की सीमा के भीतर होनी चाहिए। | BR-03 |
| LAMS_VR_Terms_Locked | Product, amount and tenure can't be changed after the application is submitted. | आवेदन जमा होने के बाद उत्पाद, राशि और अवधि नहीं बदली जा सकती। | BR-08 |
| LAMS_VR_Approved_Amount_Too_High | Approved amount can't be more than the requested amount. | स्वीकृत राशि अनुरोधित राशि से अधिक नहीं हो सकती। | BR-25 |
| LAMS_VR_Docs_Incomplete | All mandatory documents must be verified before the application can move to Under Review. | समीक्षा के लिए भेजने से पहले सभी अनिवार्य दस्तावेज़ों का सत्यापन होना चाहिए। | BR-19 |
| LAMS_VR_Score_Eligibility_Required | An application can't be approved without a credit score and an eligibility result. | क्रेडिट स्कोर और पात्रता परिणाम के बिना आवेदन स्वीकृत नहीं किया जा सकता। | BR-11 |
| LAMS_VR_Override_Reason_Required | Enter an override reason when the credit score is entered manually. | क्रेडिट स्कोर मैन्युअल रूप से दर्ज करने पर ओवरराइड का कारण दर्ज करें। | BR-15 |
| LAMS_VR_Decision_Comments_Required | Enter decision comments when approving an application with a Refer or Fail result. | Refer या Fail परिणाम वाले आवेदन को स्वीकृत करते समय निर्णय टिप्पणी दर्ज करें। | BR-23 |
| LAMS_VR_Rejection_Reason_Required | Select a rejection reason. | अस्वीकृति का कारण चुनें। | BR-26 |
| LAMS_VR_Withdrawal_Reason_Required | Enter a reason for withdrawing the application. | आवेदन वापस लेने का कारण दर्ज करें। | BR-32 |
| LAMS_VR_Offer_Accepted_Locked | Amount, tenure and approved amount can't be changed after the offer is accepted. | ऑफ़र स्वीकार होने के बाद राशि, अवधि और स्वीकृत राशि नहीं बदली जा सकती। | BR-29 |
| LAMS_VR_Doc_Rejection_Reason_Required | Enter a reason when rejecting a document. | दस्तावेज़ अस्वीकार करते समय कारण दर्ज करें। | BR-18 |
| LAMS_VR_Waiver_Reason_Required | Enter a reason when waiving a late fee. | विलंब शुल्क माफ़ करते समय कारण दर्ज करें। | BR-51 |
| LAMS_VR_Waiver_Not_Permitted | You don't have permission to waive late fees. | आपको विलंब शुल्क माफ़ करने की अनुमति नहीं है। | BR-51 |
| LAMS_VR_Payment_Amount_Positive | Payment amount must be greater than zero. | भुगतान राशि शून्य से अधिक होनी चाहिए। | BR-41 |
| LAMS_VR_Payment_Locked | A payment's amount, loan, reference, date and mode can't be changed after it is saved. Reverse it instead. | सहेजे जाने के बाद भुगतान की राशि, ऋण, संदर्भ, तिथि और माध्यम नहीं बदले जा सकते। इसके बजाय इसे रिवर्स करें। | BR-45 |

**Settings screen, errors and portal** (used by LAMS-019, LAMS-030, LAMS-079):

| Label name | English value | Hindi value (draft) |
| --- | --- | --- |
| LAMS_Settings_Title | LAMS Settings | LAMS सेटिंग्स |
| LAMS_Settings_Features | Features | सुविधाएँ |
| LAMS_Settings_Thresholds | Thresholds | सीमा मान |
| LAMS_Settings_Save | Save | सहेजें |
| LAMS_Settings_Saved | Settings saved. | सेटिंग्स सहेजी गईं। |
| LAMS_Settings_No_Permission | You don't have permission to change LAMS settings. | आपको LAMS सेटिंग्स बदलने की अनुमति नहीं है। |
| LAMS_Settings_Invalid_Value | One or more values aren't valid. Numbers can't be negative. | एक या अधिक मान मान्य नहीं हैं। संख्याएँ ऋणात्मक नहीं हो सकतीं। |
| LAMS_Error_Settings_Missing | LAMS settings are not set up. Ask an administrator to run the settings script. | LAMS सेटिंग्स सेट नहीं हैं। किसी व्यवस्थापक से सेटिंग्स स्क्रिप्ट चलाने के लिए कहें। |
| LAMS_Error_Generic | Something went wrong. Please try again or contact support. | कुछ गलत हो गया। कृपया पुनः प्रयास करें या सहायता से संपर्क करें। |
| LAMS_Portal_Maintenance | The portal is temporarily unavailable. Please try again later. | पोर्टल अस्थायी रूप से उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें। |

That is 26 labels. The Hindi text is a draft. Have a native speaker check it before the portal goes live (BRD dependency D4).

**Source files**

| What | Metadata type | File |
| --- | --- | --- |
| English labels | `CustomLabels` | `force-app/main/default/labels/CustomLabels.labels-meta.xml` |
| Hindi label translations | `Translations` (`hi`) | `force-app/main/default/translations/hi.translation-meta.xml` |
| Hindi field labels, picklist values, validation messages (later items) | `CustomObjectTranslation` (`<Object>-hi`) | `force-app/main/default/objectTranslations/<Object>-hi/…` |

A Hindi entry in `hi.translation-meta.xml` looks like this:

```xml
<customLabels>
    <label>राशि उत्पाद की न्यूनतम और अधिकतम सीमा के भीतर होनी चाहिए।</label>
    <name>LAMS_VR_Amount_Out_Of_Range</name>
</customLabels>
```

**How each layer reads a label:** Apex `System.Label.LAMS_Error_Generic` · LWC `import LABEL from '@salesforce/label/c.LAMS_Settings_Title';` · Flow, Visualforce and formulas `{!$Label.LAMS_Portal_Maintenance}`.

## Steps

1. Create the 26 labels in Setup → Custom Labels, or write `CustomLabels.labels-meta.xml` directly (one `<labels>` block each: `fullName`, `categories`, `language` en_US, `protected` false, `shortDescription`, `value`).
2. Deploy: `sf project deploy start --metadata CustomLabels`.
3. Add Hindi in one of two ways:
   - Setup → Translation Workbench → Translate → Language *Hindi*, Setup Component *Custom Label*. Enter each value and save. Or open the label and use **Local Translations / Overrides → New**.
   - Or write `translations/hi.translation-meta.xml` with one `<customLabels>` block per label.
4. Retrieve labels and translations **in the same request**: `sf project retrieve start --metadata CustomLabels Translations:hi`.
5. Check: change your own user's Language to Hindi (or log in as a Hindi test user later). Then run `echo "System.debug(System.Label.LAMS_Settings_Saved);" | sf apex run`. Expect the Hindi text. Set the language back.
6. Commit: `feat(i18n): first set of custom labels with Hindi translations [LAMS-021]`.

## Learn

- **Translations are separate metadata.** Custom label translations live in `Translations` (one file per language). Field, picklist and validation-message translations live in `CustomObjectTranslation`. A retrieve returns translations only for the components named in the **same** request, so always retrieve `CustomLabels` together with `Translations:hi`.
- **Validation rule messages can't reference `$Label`.** The rule's Error Message is plain text, and its Hindi version is entered in Translation Workbench (component *Validation Error Message*) in LAMS-031/032. The label stays the single source of truth because the M05 tests assert `System.Label.X` against the rule's message. That keeps the two from drifting.
- The language shown is the **user's** language (`LanguageLocaleKey`). The borrower's `Preferred_Language__c` picks email templates (BR-54, LAMS-062), but portal labels follow the portal user's language setting.
- A label used in Apex or LWC can't be deleted while it is referenced, and labels count toward metadata size. Reuse one label instead of creating near-duplicates.

## Done when

- [ ] 26 labels exist with the names, categories and English values above, in `labels/CustomLabels.labels-meta.xml`
- [ ] Each label has a Hindi translation, stored in `translations/hi.translation-meta.xml`
- [ ] With the running user's language set to Hindi, `System.Label.LAMS_Settings_Saved` returns the Hindi text
- [ ] `sf project deploy start --dry-run` succeeds for `CustomLabels` and `Translations:hi`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §12 Custom labels, §13.1 Validation rules, §15 Portal (maintenance message), §8 dependency D4, BR-54, BR-61, NFR-09, NFR-12
