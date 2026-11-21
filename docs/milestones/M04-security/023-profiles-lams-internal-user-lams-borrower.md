# LAMS-023 · Profiles: LAMS Internal User, LAMS Borrower, Integration

**Milestone:** [M04 – Security](README.md) · **Size:** M (2–5h) · **Delivers:** §11

**Depends on:** LAMS-022; M02 done (record types and layouts exist, including the Account record types from LAMS-094)

## Goal

Each user gets a minimal profile that handles only what a profile must: licence, page layout and default record type assignments, default app and login settings. All LAMS object and field access then comes from permission sets (LAMS-024). This keeps least privilege (NFR-06), and BR-71 hiding works because nothing is granted twice.

## Build

| Profile | Built from | User licence | Used by |
| --- | --- | --- | --- |
| LAMS Internal User | Clone of **Standard User**, stripped | Salesforce | Loan Officer 1, Operations Officer 1 (the full-licence staff who work Leads and Cases) |
| LAMS Internal Platform User (proposed) | Clone of **Standard Platform User**, stripped the same way | Salesforce Platform | Credit Manager, Loan Officer 2, Operations Officer 2 |
| LAMS Borrower | Clone of **Customer Community Login User** | Customer Community Login | Portal borrowers (self-registration default profile in LAMS-074) |
| System Administrator | Standard, unchanged | Salesforce | You; in this org the admin also acts as the Credit Head (LAMS-029) |
| Minimum Access - API Only Integrations | Standard, unchanged (proposed: no clone needed) | Salesforce Integration | Integration User (created in LAMS-068) |

**LAMS Internal User: what to keep and strip**

| Area | Setting |
| --- | --- |
| LAMS custom objects | **No** object permissions. Permission sets grant them |
| Account, Contact | Read, Create, Edit (no Delete). Staff capture borrowers (an Individual Borrower or Business Borrower Account plus the borrower Contact) and Operations handles Address Change requests (proposed) |
| Contact FLS | `PAN__c`, `Monthly_Income__c` **not visible** (opened for staff who need them by permission sets, LAMS-027). |
| Case, Task, Event | Read, Create, Edit (proposed; service requests and follow-up tasks) |
| Lead, Campaign | No access on the profile. LAMS_Sales_Access grants Lead and Campaign read, LAMS_Policy_Admin grants Campaign create/edit (LAMS-024) |
| Opportunity, Contract, Order, Quote, Price Book, Product | No access |
| System permissions | Remove Run Reports, Export Reports, Create and Customize Reports (LAMS_Reports grants them), API Enabled, Manage Public List Views. Keep Lightning Experience User |
| Page layouts | Loan_Application__c record types Personal/Home/Auto/Business → their own layouts. Loan__c, Loan_Product__c, Case (Loan Service Request) → their LAMS layouts. Account: Individual Borrower → Individual Borrower Layout, Business Borrower → Business Borrower Layout; Contact → Borrower Layout (LAMS-015) |
| Record types | Loan_Application__c: all 4, default Personal. Case: Loan Service Request (default). Account: Individual Borrower (default) and Business Borrower |
| Default app | LAMS |
| Tab settings | LAMS tabs *Default On* (object access still comes from permission sets) |

**LAMS Internal Platform User (proposed): differences from LAMS Internal User**

The licence plan for the `Lams` org (2 free full Salesforce licences, 6 Salesforce Platform) puts three staff users on Salesforce Platform (LAMS-029). A profile is tied to its licence, so they need their own profile. Set it up exactly like LAMS Internal User, except:

| Area | Setting |
| --- | --- |
| Case | Not available on the Platform licence. These users never see service requests; Disputes route to the Credit Head queue instead (LAMS-078) |
| Lead, Campaign | Not available on the Platform licence, whatever a permission set grants (LAMS-024) |
| Page layouts, record types | Same as LAMS Internal User, without the Case rows |

**LAMS Borrower**

| Area | Setting |
| --- | --- |
| LAMS custom objects | No object permissions (LAMS_Borrower_Portal grants them) |
| Account, Contact | Read (own records through the portal) |
| Case | Read, Create |
| Page layouts | Portal-specific layouts if you make them in M10; otherwise the record-type layouts |
| Record types | Loan_Application__c: all 4 (the New Loan Application flow sets the type). Case: Loan Service Request. Account: Individual Borrower (default; self-registration creates an Individual Borrower Account and Contact, LAMS-074) |
| Password policy | Defaults |

**Integration:** the Salesforce Integration licence works only with the *Minimum Access - API Only Integrations* profile. The user's access comes from the **Salesforce API Integration** permission set licence plus `LAMS_Integration` (LAMS-024). The user itself is created in LAMS-068.

## Steps

1. Setup → Profiles → *Standard User* → Clone → `LAMS Internal User`. Edit it, using the enhanced profile UI, to match the table. Then clone *Standard Platform User* → `LAMS Internal Platform User` and apply the same settings minus Case.
2. Clone *Customer Community Login User* → `LAMS Borrower`. Digital Experiences must already be on (LAMS-005).
3. Assign page layouts per record type (Object Manager → Loan Application → Page Layouts → Page Layout Assignment, and the same for Account) and set record type defaults on all three profiles.
4. Retrieve the profiles **together with** the objects, layouts and record types they reference, or the profile files come back nearly empty:
   `sf project retrieve start --metadata "Profile:LAMS Internal User" "Profile:LAMS Internal Platform User" "Profile:LAMS Borrower" CustomObject:Loan_Application__c CustomObject:Loan__c CustomObject:Loan_Product__c CustomObject:Account CustomObject:Contact Layout RecordType CustomApplication:LAMS`
5. Look over the profile XML. Remove `<userPermissions>` you didn't mean to keep and any unrelated objects. Keep the file small.
6. Commit: `feat(security): LAMS Internal User, LAMS Internal Platform User and LAMS Borrower profiles [LAMS-023]`.

## Learn

- **Profiles vs permission sets:** every user has exactly one profile, but can have many permission sets. Page layout assignments, default record type and login hours/IP ranges still live **only** on profiles. Everything else belongs in permission sets, and Salesforce is moving that way.
- **Profile retrieve gotcha:** a profile's permissions come back only for components named in the *same* retrieve. Retrieving `Profile:X` alone gives you an almost empty file, and deploying that file doesn't remove access in the org.
- A cloned profile keeps the source profile's licence. You can't turn a Salesforce-licence profile into a portal one, or a Platform one, later. That is why the Platform users need their own clone.
- **Licence limits beat permissions:** a Salesforce Platform user can't use Leads, Campaigns, Cases or Opportunities, and can't even be assigned a permission set that grants them (hence LAMS_Sales_Access and LAMS_Case_Access, LAMS-024). Check a user's licence first when an object is missing.
- Hiding `PAN__c` at the profile and opening it only by permission set means there is one place to look when checking AC-14.

## Done when

- [ ] `LAMS Internal User` (Salesforce licence), `LAMS Internal Platform User` (Salesforce Platform licence) and `LAMS Borrower` (Customer Community Login licence) exist and match the tables
- [ ] On both internal profiles, PAN__c and Monthly_Income__c are not visible and no LAMS custom object has object permissions
- [ ] Each application record type opens its own layout for a LAMS Internal User
- [ ] The three profile files are in `force-app/main/default/profiles/` and deploy cleanly
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Profiles and Field-level security, §15 Page layouts and Application record pages, §19 users list, BR-70, BR-71, NFR-06
