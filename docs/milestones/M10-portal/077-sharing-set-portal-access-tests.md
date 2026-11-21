# LAMS-077 · Sharing set + portal access tests

**Milestone:** [M10 – Portal](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-59

**Depends on:** LAMS-074 (site and LAMS Borrower members), LAMS-026 (Private OWDs), LAMS-029 (two portal borrowers), LAMS-076 (pages to test through)

## Goal

A borrower sees only their own applications, documents, loans, instalments, payments and requests, and cannot open another borrower's application even by URL (BR-59, **AC-13**).

## Build

**Sharing set** *LAMS Borrower Sharing Set* (proposed name; Setup → Digital Experiences → Settings → Sharing Sets), profile **LAMS Borrower**.

| Object | User field | Target record field | Access |
| --- | --- | --- | --- |
| Loan_Application__c | Contact | `Loan_Application__c.Borrower__c` | Read/Write (draft save, Respond to Offer, Withdraw) |
| Loan__c | Contact | `Loan__c.Borrower__c` | Read Only |
| Case | Contact | `Case.ContactId` | Read/Write (proposed; add details to own request) |
| Contact (proposed) | Contact | `Contact.Id` | Read Only — so the flow can set `Borrower__c` to the user's own Contact |
| Account (proposed) | Account | `Account.Id` | Read Only |

Child objects follow their parent (Controlled by Parent): Application_Document__c, EMI_Instalment__c, Payment__c (§11).

**Test class `PortalAccessTest`** (proposed name) — proves AC-13 in code:

| Setup | Assert |
| --- | --- |
| Internal owner with a role (`System.runAs` to avoid mixed DML); two Accounts/Contacts A and B; two LAMS Borrower users; one application, document, loan, instalment and payment per borrower | – |
| `System.runAs(userA)`: `SELECT Id FROM Loan_Application__c` | Only A's application |
| `System.runAs(userA)`: `SELECT Id FROM Loan_Application__c WHERE Id = :appB` | 0 rows |
| `SELECT HasReadAccess FROM UserRecordAccess WHERE UserId = :userA AND RecordId = :appB` | false (same for B's loan, payment and case) |
| `System.runAs(userA)`: update B's application | `DmlException` (insufficient access) |
| User A on own loan's EMI rows and payments | Visible |

## Steps

1. Create the sharing set with the rows above.
2. Retrieve it: `sf project retrieve start --metadata SharingSet` (if your org does not return it, record it as a manual step in the README).
3. Write `PortalAccessTest`; run `sf apex run test --class-names PortalAccessTest --result-format human`.
4. **Manual AC-13 check:** log in as borrower A; open B's application by pasting `https://<mydomain>.my.site.com/borrowers/s/loan-application/<B's Id>` → the page shows that the record is not available; repeat for B's loan and case.
5. Take a screenshot of the refusal for `docs/BRD/images/`.
6. Commit: `feat(security): borrower sharing set and AC-13 access tests [LAMS-077]`.

## Learn

- **Sharing sets work only for high-volume portal licences** (Customer Community, Customer Community Login): these users have no role, so sharing rules and role hierarchy cannot reach them. Access is granted by matching a field on the record to the user's Contact or Account.
- Sharing sets give access *to* portal users; for internal users to see portal-owned records you use share groups or ownership/assignment (here, owner reassignment in LAMS-037 and Case queues in LAMS-078).
- Hiding a page or link is not security. AC-13 is proved only by testing access to the record Id directly.
- `UserRecordAccess` is the quickest way to assert sharing in Apex tests.

## Done when

- [ ] **AC-13:** logged in as borrower A, opening borrower B's application by URL is refused (screenshot saved)
- [ ] Borrower A sees own applications, documents, loans, instalments, payments and cases, and none of B's
- [ ] `PortalAccessTest` passes, covering application, loan, payment and case
- [ ] Sharing set in source or listed as a manual step in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Sharing (portal sharing set), OWD table, profiles; §9 AC-13; BR-59; §20 step 4 (AC-13)
