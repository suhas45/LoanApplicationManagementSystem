# LAMS-029 · Test users and group assignments

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** §19

**Depends on:** LAMS-022, LAMS-023, LAMS-025; LAMS-016 (demo borrower Contacts)

## Goal

The org has the demo cast from §19: two Loan Officers, a Credit Manager, a Credit Head, two Operations Officers and two portal borrowers. Each one has the right role, profile and permission set group, so every access rule can be shown by logging in as a real user. This is the M04 exit (AC-14) and later AC-06 and AC-13.

## Build

Usernames must be unique across all Salesforce orgs. Use a suffix such as `@lams-<yourinitials>.demo` (proposed). Use your own inbox for Email so notifications arrive. For every user: Locale *English (India)*, Time Zone *Asia/Kolkata*, Email Encoding UTF-8.

| User (proposed names) | Alias | Role | Profile | Assignment | Language |
| --- | --- | --- | --- | --- | --- |
| Priya Sharma – Loan Officer 1 | psharma | Loan_Officer | LAMS Internal User | Group LAMS Loan Officer | English |
| Rahul Verma – Loan Officer 2 | rverma | Loan_Officer | LAMS Internal User | Group LAMS Loan Officer | English |
| Anita Desai – Credit Manager | adesai | Credit_Manager | LAMS Internal User | Group LAMS Credit Manager | English |
| Vikram Rao – Credit Head | vrao | Credit_Head | LAMS Internal User | Group LAMS Credit Head | English |
| Suresh Iyer – Operations Officer 1 | siyer | Operations_Officer | LAMS Internal User | Group LAMS Operations | English |
| Meera Nair – Operations Officer 2 | mnair | Operations_Officer | LAMS Internal User | Group LAMS Operations | English |
| Borrower 1 (demo Contact from LAMS-016) | – | – | LAMS Borrower | Permission set LAMS_Borrower_Portal | English |
| Borrower 2 (demo Contact from LAMS-016) | – | – | LAMS Borrower | Permission set LAMS_Borrower_Portal | **Hindi** (and Contact.Preferred_Language__c = Hindi, BR-54) |

- Set **Manager** on each Loan Officer to Anita Desai (proposed; useful for approval reminders and reports).
- The Accounts of the two borrower Contacts must be **owned by a user with a role**. Set the owner to Priya Sharma.
- The **Integration User** from §19 is created in LAMS-068 with its own licence.
- Queue memberships (Credit Managers, Operations) come in LAMS-078.

**Licences:** check Setup → Company Information → User Licenses against what you recorded in LAMS-002. If the org has fewer Salesforce licences than staff users, drop Loan Officer 2 and Operations Officer 2 first (milestones README risk table: "Trim demo users"). Write down what you dropped.

**Script (proposed): `scripts/apex/create-test-users.apex`**. Anonymous Apex that:

1. Looks up the Profile, UserRole and PermissionSetGroup Ids by name (never hardcoded Ids).
2. Inserts the 6 staff users and the 2 portal users (portal users with `ContactId` set). Use `Database.DMLOptions` with `EmailHeader.triggerUserEmail = false` so no welcome emails go out.
3. Inserts `PermissionSetAssignment` rows: `PermissionSetGroupId` for the groups and `PermissionSetId` for LAMS_Borrower_Portal.
4. Skips any user whose Username already exists, so it is safe to re-run.

## Steps

1. Write the script, or create the users in Setup → Users and assign groups from each user's *Permission Set Group Assignments* related list.
2. Run it: `sf apex run --file scripts/apex/create-test-users.apex`.
3. Check: `sf data query --query "SELECT Username, Profile.Name, UserRole.Name, IsActive FROM User WHERE Username LIKE '%@lams-%'"` and `sf data query --query "SELECT Assignee.Username, PermissionSetGroup.DeveloperName, PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username LIKE '%@lams-%'"`.
4. Turn on Setup → Login Access Policies → *Administrators Can Log in as Any User*. Log in as each user once.
5. Run the AC-14 check from LAMS-027 as Suresh Iyer.
6. Commit the script: `chore(security): demo users and permission set group assignments [LAMS-029]`.

## Learn

- **Users can't be deleted**, only deactivated or frozen, and a used username can't be reused in any org. Pick usernames once.
- `sf org create user` works only for scratch orgs. In a Developer Edition, create users in Setup, by Apex or through the API.
- **Mixed DML:** User and PermissionSetAssignment are both setup objects, so they can share a transaction. Inserting a Contact or Account in the same transaction can't. Create borrower Contacts first (LAMS-016), then the portal users.
- `sf org assign permset` assigns permission sets, not permission set groups. For groups, use the UI or a `PermissionSetAssignment` with `PermissionSetGroupId`.

## Done when

- [ ] The 6 staff users exist with the roles, profile and groups in the table (or the trimmed set, written down)
- [ ] 2 portal users exist on LAMS Borrower with LAMS_Borrower_Portal; Borrower 2's language is Hindi
- [ ] Logged in as Priya, the LAMS app opens and she can create a Draft application; as Anita, the Loan Product Edit button is missing; as Vikram, it is present
- [ ] AC-14 passes logged in as Suresh Iyer (M04 exit criterion)
- [ ] The user script (if used) is committed under `scripts/apex/` and contains no hardcoded Ids
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Org setup checklist (users), §11 Profiles, Role hierarchy, Permission set groups, §8 constraint C1, §9 AC-06, AC-13, AC-14, BR-54, BR-70
