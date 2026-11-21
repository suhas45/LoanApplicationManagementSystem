# LAMS-074 · Site on Aura Customer Service template, self-registration with PAN check

**Milestone:** [M10 – Portal](README.md) · **Size:** M (2–5h) · **Delivers:** BR-59

**Depends on:** LAMS-005 (Digital Experiences enabled), LAMS-008 (Contact `PAN__c` + Duplicate Rule), LAMS-023 (LAMS Borrower profile), LAMS-024 (`LAMS_Borrower_Portal`), LAMS-021 (custom labels + Hindi), LAMS-029 (portal borrower users, internal users with roles)

## Goal

Stand up the **LAMS Borrower Portal** on the Aura Customer Service template, and let a new borrower register themselves: registration creates their own Account and Contact and refuses a PAN that already exists (BR-02, BR-59, §15).

## Build

**Site**

| Setting | Value |
| --- | --- |
| Name | LAMS Borrower Portal |
| Template | Customer Service (Aura) |
| URL path | `borrowers` (proposed) → `https://<mydomain>.my.site.com/borrowers` |
| Members (Administration → Members) | Profile **LAMS Borrower** (Customer Community Login); System Administrator for testing |
| Public access | Off (Settings → *Public can access the site* unticked): only Login, Register and Forgot Password are public (proposed) |
| Languages | English (default), Hindi (Builder → Settings → Languages), NFR-12 |
| Guest record default owner | An active internal user **with a role** (proposed: the Credit Head user); records created during registration are owned by this user (Administration → Preferences / guest user settings) |
| Login & Registration | *Allow customers and partners to self-register* on; Registration page type = Experience Builder page *Register*; Profile = LAMS Borrower |

**Registration page** — replace the template's register component with LWC **`borrowerSelfRegister`** (proposed name), target `lightningCommunity__Page`, calling **`BorrowerSelfRegController`** (proposed name).

| Form field | Saved to | Rule |
| --- | --- | --- |
| First name, Last name | Contact, Account Name, User | Required |
| Email | Contact.Email, User.Email; Username = email + `.lams` (proposed suffix) | Required, valid email |
| Mobile | Contact.MobilePhone | Required |
| Date of birth | Contact.Birthdate | Required; age ≥ 18 (proposed) |
| PAN | Contact.PAN__c | Required; regex `[A-Z]{5}[0-9]{4}[A-Z]`; upper-cased |
| Preferred language | Contact.Preferred_Language__c | English / Hindi |
| Password + confirm | `Site.createExternalUser` | Org password policy |

**Controller** `public without sharing class BorrowerSelfRegController` (guest context cannot query Contacts; keep the class small and return no data).

| Method | Behaviour |
| --- | --- |
| `@AuraEnabled public static String register(RegistrationRequest req)` | 1) validate fields; 2) `SELECT Id FROM Contact WHERE PAN__c = :pan LIMIT 1` → if found, throw `AuraHandledException` with label `LAMS_Portal_PAN_Already_Registered` (proposed): "This PAN is already registered; sign in or contact your branch" — never reveal the name; 3) insert Account (one per borrower, avoids account skew, §10.1); 4) insert Contact; 5) `Site.createExternalUser(user, accountId, password)`; 6) assign `LAMS_Borrower_Portal` in an `@future` method (mixed DML); 7) return `Site.login(username, password, startUrl).getUrl()` |
| Errors | Any DML error rolls back with `Database.setSavepoint`/`rollback`; messages come from custom labels (EN/HI) |

Guest user profile (*LAMS Borrower Portal Profile*, created with the site): Apex Class Access to `BorrowerSelfRegController` only; no object access needed.

**Test class `BorrowerSelfRegControllerTest`:** valid registration (Account + Contact created; `Site.createExternalUser` returns null in tests, so assert the records and handle null), duplicate PAN refused, bad PAN format refused, missing field refused.

## Steps

1. Create the site from the CLI (or Setup → Digital Experiences → New):
   `sf community create --name "LAMS Borrower Portal" --template-name "Customer Service" --url-path-prefix borrowers`
2. In Setup → Digital Experiences → Settings, turn on *Enable ExperienceBundle Metadata API* so the site can be retrieved as source.
3. Workspaces → Administration: Members, Login & Registration, Preferences, guest default owner as in the table.
4. Build `BorrowerSelfRegController` + test, then `borrowerSelfRegister` (with Jest tests for validation messages); deploy.
5. In Experience Builder open the *Register* page, remove the standard self-registration component, drop `borrowerSelfRegister`; publish:
   `sf community publish --name "LAMS Borrower Portal"`
6. Register a new borrower in a private browser window; register again with the same PAN and see the refusal.
7. Retrieve (check real names first with `sf org list metadata --metadata-type Network`):
   `sf project retrieve start --metadata ExperienceBundle Network CustomSite ApexClass:BorrowerSelfRegController LightningComponentBundle:borrowerSelfRegister`
8. Record in the README what is manual: guest default owner, Members, Login & Registration choices, publishing, Hindi enablement in Builder.
9. Commit: `feat(portal): LAMS Borrower Portal site with PAN-checked self-registration [LAMS-074]`.

## Learn

- **Aura templates vs LWR:** Customer Service is an Aura template; it supports custom Aura theme layouts (LAMS-075). LWR is newer and faster but is not used here on purpose (§15).
- **Guest user security:** guest users own nothing; records they create go to the site's default owner, who must have a role for portal users to be created under the Account.
- **`without sharing` in guest context** must be narrow: check, create, return nothing sensitive. A PAN lookup that answered "registered to Ravi Kumar" would be a data leak.
- Not everything deploys: the ExperienceBundle carries pages and theme; membership, some login settings and publishing are org steps.

## Done when

- [ ] The site is live at the `borrowers` URL; only Login, Register and Forgot Password are reachable without login
- [ ] A new borrower can register; an Account, a Contact with PAN and a LAMS Borrower user exist; the user has `LAMS_Borrower_Portal`
- [ ] Registering with an existing PAN is refused with the EN/HI label and creates nothing (BR-02)
- [ ] `BorrowerSelfRegControllerTest` passes with ≥ 90% coverage
- [ ] Site metadata is in source; manual steps are listed in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §15 Portal (Experience Cloud), §10.1 Contact and one Account per borrower, §11 LAMS Borrower profile and `LAMS_Borrower_Portal`, §19 Not in source, BR-02, BR-54, BR-59, NFR-11, NFR-12, D1, C1
