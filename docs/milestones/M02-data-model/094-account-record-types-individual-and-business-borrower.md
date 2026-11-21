# LAMS-094 · Account record types Individual Borrower and Business Borrower (no Person Accounts)

**Milestone:** [M02 – Data model](README.md) · **Size:** S (≤ 2h) · **Delivers:** BRD §10.1, §19, C1–C2

**Depends on:** M01 done (LAMS-002 org signed up, LAMS-003 CLI authorised to alias `Lams`). No other LAMS item. Do it **first in M02**, before LAMS-007 – LAMS-016 and before any Account record type, layout or borrower data exists.

## Goal

Every borrower has the same shape: **one Account per borrower plus a Contact who is the borrower** (Borrower__c, §10.1, A1). An individual (Personal, Home, Auto) gets an Account with record type **Individual Borrower**, named after the person, with exactly one Contact. A Small-Business borrower gets an Account with record type **Business Borrower**, with the director as its Contact. Contact sharing is set to **Controlled by Parent**, so a borrower's Account and Contact always share one owner and one set of shares (§11, C2). Lead conversion (BR-87, LAMS-098), the portal sharing set (LAMS-077) and the seed data (LAMS-016) all build on this.

**Person Accounts are not enabled in LAMS.** BRD v2.2 planned them (BRD Appendix D1). The team chose the standard Account + Contact model instead, for three reasons:

- **Irreversible.** Once Person Accounts are on, they can't be turned off. They change the Account and Contact data model for the life of the org (person fields on Account, `__pc` fields, a hidden Contact behind each Account).
- **One model for both borrower types.** Small-Business borrowers need an Account plus a Contact anyway. Using the same shape for individuals means one set of queries, layouts, flows and tests.
- **Fewer surprises in a portfolio org.** Some orgs need a Support case to enable Person Accounts. Several features behave differently with them: Contact automation, lead conversion and record-type defaults.

The BRD text about Person Accounts (`__pc` fields, `PersonContactId`, `IsPersonAccount`) does not apply. The decision is recorded in BRD Appendix D1.

## Build

**Contact org-wide default** (Setup → Sharing Settings)

| Object | Internal | External | Why |
| --- | --- | --- | --- |
| Contact | **Controlled by Parent** | Controlled by Parent | A design choice here, not a platform requirement. A borrower's Contact has no sharing of its own and follows its Account. Officers, managers and the portal sharing set (LAMS-077, which matches on `User.AccountId`) only ever open the Account. LAMS-026 confirms this setting and sets the other OWDs |

**Check that nothing relies on the Contact OWD before you change it.** In a fresh Developer Edition org, all four checks should come back empty or default:

| Check | Where | Expected |
| --- | --- | --- |
| Contact sharing rules | Setup → Sharing Settings → Contact Sharing Rules | None |
| Contact access on roles | Setup → Roles (none yet; created in LAMS-022) | – |
| Apex or flows that query Contacts | Setup → Apex Classes, Flows | Only the Developer Edition samples, if any |
| Experience Cloud sites | Setup → Digital Experiences → All Sites | None yet (the site is LAMS-074) |

If any check finds something, note it in the milestone Parking lot before you change the OWD.

**Account record types** (Object Manager → Account → Record Types)

| Record type (DeveloperName) | Label | Used for | Account Name holds | Contacts | Active |
| --- | --- | --- | --- | --- | --- |
| `Individual_Borrower` | Individual Borrower | Personal, Home and Auto borrowers | The person's full name, for example *Aarav Sharma* | Exactly one: the borrower (convention, proposed; see below) | Yes |
| `Business_Borrower` | Business Borrower | Small-Business borrowers | The business name, for example *Iyer Traders* | The director (Borrower__c on the application); other contacts allowed | Yes |

Description on each record type: "LAMS borrower – one Account per borrower (BRD §10.1)". Keep the *Master* record type unused.

**One Account per borrower (convention, proposed)**

- Never put two unrelated borrowers under one Account. A shared "Retail Customers" Account would give one Account thousands of Contacts. That causes **account data skew**: slow sharing recalculation and record locking on every Contact save. One Account each avoids it (§10.1).
- An Individual Borrower Account has one Contact. Later items create the pair together: seed data (LAMS-016), self-registration (LAMS-074), partner API (LAMS-069) and lead conversion (LAMS-098).
- A borrower Contact always has an Account. With Controlled by Parent, a Contact without an Account is visible only to its owner and admins.
- One Contact per PAN (unique `PAN__c`, LAMS-008). A person who borrows personally and is also a business director stays one Contact, under the Account where they were first created. This is a known limitation, out of scope.

**Page layouts** (Object Manager → Account → Page Layouts). Create them now with the standard fields; LAMS-015 completes them.

| Layout | Record type | Sections now |
| --- | --- | --- |
| Individual Borrower Layout | Individual_Borrower | Account Information (Account Name, Account Owner, Phone); Address (Billing Address); System Information. Related lists: Contacts. LAMS-015 adds Loan Applications, Loans and Cases |
| Business Borrower Layout | Business_Borrower | Account Information (Account Name, Account Owner, Phone, Website, Industry); Address (Billing Address); System Information. Related lists: Contacts (directors) |

**Record type assignment now** (Profiles → System Administrator → Record Type Settings → Account):

| Profile | Available | Default |
| --- | --- | --- |
| System Administrator | Individual Borrower, Business Borrower | Individual Borrower |

LAMS-023 repeats this for its profiles. LAMS Internal User gets both, default Individual Borrower. LAMS Borrower gets Individual Borrower only (self-registration, LAMS-074). The default matters: a lead converted with the standard *Convert* button creates its Account with the converting user's default record type (LAMS-098).

**What this means for later items**

| Item | Effect |
| --- | --- |
| LAMS-008 | Borrower fields live on Contact only; no fields on Account |
| LAMS-015 | Completes both Account layouts and adds a record page per record type |
| LAMS-016 | Seed borrowers load as 6 Individual Borrower Accounts, each with one Contact, plus Iyer Traders (Business Borrower) with director Kavya Iyer |
| LAMS-023 | Record type visibility and defaults per profile, as above |
| LAMS-026 | Contact OWD is already Controlled by Parent; only confirm it |
| LAMS-033 | `TestDataFactory.createBorrower` inserts an Individual_Borrower Account and its Contact and returns the Contact |
| LAMS-077 | The sharing set matches the borrower's Account (`User.AccountId`); Contacts follow it |
| LAMS-098 | Conversion puts an individual lead into an Individual_Borrower Account and a business lead into a Business_Borrower Account |

## Steps

1. Optional but recommended (proposed): delete the sample records that Developer Edition ships with. The org has 5 MB of data storage, and sample Accounts and Leads would also clutter the duplicate rules and sales reports later. In Execute Anonymous, delete in this order: `delete [SELECT Id FROM Opportunity]; delete [SELECT Id FROM Case]; delete [SELECT Id FROM Contact]; delete [SELECT Id FROM Account]; delete [SELECT Id FROM Lead]; delete [SELECT Id FROM Campaign];`
2. Run the four checks above.
3. Setup → Sharing Settings → Edit → Contact: *Controlled by Parent* (internal and external). Save, then wait for the recalculation email.
4. Object Manager → Account → Record Types → New: create `Individual_Borrower`, then `Business_Borrower`. For each one, choose *Apply a new layout* and create the layout from the table. In the profile step, make both available to System Administrator only, with Individual Borrower as the default.
5. Edit both layouts as in the table.
6. Smoke test. Save as `scripts/apex/check-borrower-record-types.apex` (proposed) and run `sf apex run --file scripts/apex/check-borrower-record-types.apex --target-org Lams`:
   ```apex
   Map<String, Schema.RecordTypeInfo> rts = Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName();
   Account a = new Account(Name = 'Test Borrower', RecordTypeId = rts.get('Individual_Borrower').getRecordTypeId());
   insert a;
   insert new Contact(FirstName = 'Test', LastName = 'Borrower', AccountId = a.Id);
   System.debug([SELECT RecordType.DeveloperName, (SELECT Id FROM Contacts) FROM Account WHERE Id = :a.Id]);
   delete a; // deletes its Contact too
   ```
7. Check: `sf data query --query "SELECT DeveloperName, IsActive FROM RecordType WHERE SobjectType = 'Account'" --target-org Lams` returns both record types, active.
8. Retrieve:
   `sf project retrieve start --metadata RecordType:Account.Individual_Borrower RecordType:Account.Business_Borrower "Layout:Account-Individual Borrower Layout" "Layout:Account-Business Borrower Layout" CustomObject:Contact --target-org Lams`
   The Contact OWD is stored as `<sharingModel>ControlledByParent</sharingModel>` in `objects/Contact/Contact.object-meta.xml`.
9. Add a line to the README's manual-steps list (finished in LAMS-092): sample data deleted, Contact OWD changed, Person Accounts deliberately not enabled.
10. Commit: `feat(data-model): Individual and Business Borrower account record types, Contact controlled by parent [LAMS-094]`.

## Learn

- **Person Accounts are a one-way door.** Enabling them is permanent. It adds person fields to Account and shows every Contact custom field on Account with a `__pc` suffix. Some orgs need a Salesforce Support case to enable them. Decide before any data exists. LAMS decided against them, and this item records why.
- **Controlled by Parent** removes Contact sharing entirely: whoever can see the Account sees its Contacts. That is why the portal sharing set (LAMS-077) targets the Account, not the Contact.
- **Account data skew:** more than about 10,000 child records under one Account slows sharing calculations and causes lock errors. One Account per borrower is the standard fix.
- **Record type defaults are per profile.** Automation that doesn't set `RecordTypeId` (for example the standard lead *Convert* button) uses the running user's default. Set defaults on purpose, and look record types up by DeveloperName, never by Id.

## Done when

- [ ] Contact OWD is Controlled by Parent (internal and external), and the four pre-checks are recorded as empty (or listed in the Parking lot)
- [ ] `Individual_Borrower` and `Business_Borrower` exist on Account, both active, each with its own layout; System Administrator defaults to Individual Borrower
- [ ] The smoke script creates an Individual Borrower Account with one Contact, and deleting the Account removes the Contact
- [ ] Person Accounts are **not** enabled (Setup → Account Settings shows them off), and the decision is written in the BRD (§10.1, §19) and the README manual-steps list
- [ ] Record types, layouts and the Contact object file are in `force-app/`; `sf project deploy start --dry-run --source-dir force-app --target-org Lams` succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.1 Borrower (one Account per borrower, Borrower__c lookup to Contact), §11 Org-wide defaults (Contact Controlled by Parent), §19 org setup checklist, §8 A1, Appendix C (C1, C2), BR-87
