# LAMS-008 · Contact custom fields + PAN Duplicate Rule

**Milestone:** [M02 – Data model](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-02

**Depends on:** M01 done. Independent of LAMS-007.

## Goal

The standard Contact becomes the borrower record, identified by PAN: one record per PAN, with a second one blocked by both a unique field and a friendly duplicate message (BR-02). The income, existing-EMI, KYC and language fields are what eligibility (BR-10, BR-11) and notifications (BR-54) read later.

## Build

**Contact fields** (Birthdate is the standard field, used for age at maturity; nothing to build)

| Field (API name) | Type | Details |
| --- | --- | --- |
| PAN__c | Text(10) | Unique (case-insensitive), External ID. Not required at field level (proposed), so non-borrower contacts can still be saved; required on the borrower layout (LAMS-015) and in the flows |
| Employment_Type__c | Picklist (restricted) | Salaried, Self-Employed, Business |
| Monthly_Income__c | Currency(16,2) | |
| Existing_EMI__c | Currency(16,2) | Default 0 (proposed), so EMI_To_Income__c never adds a blank. Other lenders' EMIs |
| KYC_Status__c | Picklist (restricted) | Pending (default), Verified, Rejected |
| KYC_Verified_Date__c | Date | Reused when within KYC_Reuse_Months__c (BR-10) |
| Preferred_Language__c | Picklist (restricted) | English (default), Hindi. Picks the template language (BR-54) |
| Repayment_Score__c | Number(3,0) | 0–100 (proposed range). Written back from Data Cloud (LAMS-089) |
| Pre_Approved__c | Checkbox | Default false. Written back from Data Cloud |

Picklist value API names equal their labels (for example `Self-Employed`), here and in every later item, so flows and Apex compare against the visible text.

**Validation rule (proposed)** `Contact_PAN_Format`: `AND(NOT(ISBLANK(PAN__c)), NOT(REGEX(PAN__c, "[A-Z]{5}[0-9]{4}[A-Z]")))`, message "PAN must be 10 characters: 5 capital letters, 4 digits, 1 capital letter (for example ABCDE1234F)." The message moves to a custom label in LAMS-021.

**Matching rule** `LAMS_Contact_PAN` (label *LAMS Contact PAN*) on Contact: `PAN__c` *Exact*, *Match blank fields* off. Activate it.

**Duplicate rule** `LAMS_Contact_PAN_Duplicate` (label *LAMS Contact PAN Duplicate*) on Contact:

| Setting | Value |
| --- | --- |
| Record-level security | *Bypass sharing rules* (Contact OWD becomes Private in LAMS-026; the check must still find contacts the user cannot see) |
| Action on create | Block |
| Action on edit | Block |
| Alert text | "A borrower with this PAN already exists. Search for the existing borrower instead of creating a new one." |
| Matching rule | `LAMS_Contact_PAN` |
| Conditions | None |
| Active | Yes |

The org's *Standard Contact Duplicate Rule* (name and email) stays as it is.

## Steps

1. Create the fields in Object Manager → Contact (or write the `.field-meta.xml` files).
2. Create the validation rule.
3. Create and **activate** the matching rule; wait until its status is *Active* (activation runs in the background).
4. Create and activate the duplicate rule.
5. Retrieve:
   `sf project retrieve start --metadata CustomField:Contact.PAN__c CustomField:Contact.Employment_Type__c CustomField:Contact.Monthly_Income__c CustomField:Contact.Existing_EMI__c CustomField:Contact.KYC_Status__c CustomField:Contact.KYC_Verified_Date__c CustomField:Contact.Preferred_Language__c CustomField:Contact.Repayment_Score__c CustomField:Contact.Pre_Approved__c ValidationRule:Contact.Contact_PAN_Format MatchingRules:Contact DuplicateRule:Contact.LAMS_Contact_PAN_Duplicate`
6. Commit: `feat(data-model): Contact borrower fields and PAN duplicate rule [LAMS-008]`.

## Learn

- **Two layers for uniqueness:** the Unique field is the hard guarantee (also for API loads and Apex), while the duplicate rule gives a readable message in the UI before the database error appears.
- **Duplicate rules need an active matching rule.** Deploying both to a fresh org in one go can fail because matching-rule activation is asynchronous; deploy the matching rule first, then the duplicate rule.
- **Bypass vs enforce sharing** in a duplicate rule decides whether a user is warned about records they cannot see. With Private contacts, *enforce* would let duplicates through.
- `REGEX()` must match the whole value, so no `^…$` anchors are needed.

## Done when

- [ ] All nine fields exist in the org and in `force-app/main/default/objects/Contact/`
- [ ] Creating a Contact with PAN `ABCDE1234F` works; a second Contact with `ABCDE1234F` is blocked with the duplicate-rule alert text
- [ ] A second Contact with `abcde1234f` is also blocked (the format rule rejects lowercase; the unique check is case-insensitive)
- [ ] PAN `ABC123` is rejected by `Contact_PAN_Format`; a Contact with no PAN saves
- [ ] `sf project deploy start --dry-run --source-dir force-app` succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.1 Contact (borrower); §11 OWD (Contact Private); §21 Duplicate rules; BR-02, BR-10, BR-11, BR-54, BR-78
