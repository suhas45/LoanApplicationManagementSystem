# LAMS-027 · FLS (PAN, income, score), View Encrypted Data

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-71, BR-72

**Depends on:** LAMS-024, LAMS-025; LAMS-012 (encrypted Payout_Account__c)

## Goal

PAN, income and credit score are invisible to Operations on every page, list view, report and search (BR-71, AC-14). The payout account number is encrypted and masked for everyone except Operations, who need it to disburse (BR-72, NFR-06).

## Build

**Field-level security matrix** (R read · E edit · – hidden). The profile `LAMS Internal User` hides all of these (LAMS-023), so this table is the complete list of who can see them.

| Field | Loan_Officer | Credit | Operations | Borrower_Portal | Integration |
| --- | --- | --- | --- | --- | --- |
| Contact.PAN__c | R E | R | **–** | R (own) | R E |
| Contact.Monthly_Income__c | R E | R | **–** | R E (p: entered in Apply) | R E |
| Loan_Application__c.Credit_Score__c | R | R E (override, BR-15) | **–** | – (p) | – |
| Loan_Application__c.Risk_Grade__c (p) | R | R | **–** | – | – |
| Loan_Application__c.EMI_To_Income__c (p) | R | R | **–** | – | – |
| Loan_Application__c.Eligibility_Notes__c (p) | R | R | **–** | – | – |
| Loan__c.Payout_Account__c | – (p) | – (p) | R E | – | – |

The rows marked (p) are proposed. Risk grade is a band of the score, EMI-to-income is a ratio that reveals income, and eligibility notes quote both. Hiding them stops BR-71 leaking through derived fields.

**Encryption and masking (BR-72):** Payout_Account__c is a Text (Encrypted) field from LAMS-012. Confirm Mask Type *Last Four Characters Clear* and Mask Character *X* (proposed if LAMS-012 chose otherwise). **View Encrypted Data** is only in LAMS_Operations (LAMS-024), so everyone else sees `XXXXXXXX1234`.

**Automated check (proposed): `LamsFieldSecurityTest`**

| Test | Assert |
| --- | --- |
| `operationsCannotReadSensitiveFields` | As an Operations test user (LAMS Internal User + LAMS_Operations_Group, `Test.calculatePermissionSetGroup`): `Schema.sObjectType.Contact.fields.PAN__c.isAccessible()`, `Monthly_Income__c` and `Loan_Application__c.Credit_Score__c` are all false. `[SELECT PAN__c FROM Contact WITH USER_MODE]` throws `QueryException` |
| `loanOfficerCanReadSensitiveFields` | Same three are accessible for a Loan Officer user |
| `onlyOperationsViewsEncrypted` | `[SELECT PermissionsViewEncryptedData FROM PermissionSet WHERE Name = 'LAMS_Operations']` is true, and false for the other LAMS sets |

## Steps

1. In each permission set (Object Settings), set the field access from the matrix. Leave the fields hidden on the profile.
2. Check the encrypted field's mask settings on Loan__c.
3. Write `LamsFieldSecurityTest`. Create the users in a `System.runAs(new User(Id = UserInfo.getUserId()))` block to avoid mixed-DML errors.
4. Manual AC-14 run, once the LAMS-029 users exist (tick the AC-14 box then): Setup → Login Access Policies → *Administrators Can Log in as Any User* on. Log in as an Operations Officer and check the places listed under Done when.
5. Retrieve the updated permission sets with the objects (see LAMS-024 step 3) and run `sf apex run test --class-names LamsFieldSecurityTest --result-format human --wait 10`.
6. Commit: `feat(security): FLS for PAN, income, score and encrypted payout account [LAMS-027]`.

## Learn

- **FLS is enforced everywhere the platform renders data:** record pages, list views, related lists, reports, search results and the API. Custom Apex in system mode is the exception, which is why later classes use `WITH USER_MODE` or `Security.stripInaccessible`.
- **Formula fields ignore the FLS of the fields they reference.** A visible formula over a hidden field leaks the value, so the derived fields must be hidden too.
- **View Encrypted Data** is all or nothing for every Classic-encrypted field in the org. Apex always reads the decrypted value, and masking is only a display behaviour. Never write the raw value to a log (IntegrationLogger masks it, LAMS-039).
- Field history (LAMS-028) obeys FLS as well, so a hidden field's old and new values don't show in History.

## Done when

- [ ] AC-14: logged in as an Operations Officer, PAN__c, Monthly_Income__c and Credit_Score__c don't appear on the Contact or Application record page, in any list view column, in report builder field lists or in global search results
- [ ] The derived fields marked (p) are hidden from Operations too, or the decision not to hide them is noted in the Parking lot
- [ ] A Loan Officer sees `XXXXXXXX1234` for Payout_Account__c; an Operations Officer sees the full number
- [ ] `LamsFieldSecurityTest` passes
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Field-level security and Permission sets (LAMS_Operations View Encrypted Data), §10.5 Payout_Account__c, §9 AC-14, BR-71, BR-72, NFR-06
