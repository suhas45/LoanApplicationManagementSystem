# LAMS-029 · Test users and group assignments

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** §19

**Depends on:** LAMS-022, LAMS-023, LAMS-025; LAMS-016 (demo borrowers); LAMS-094 (Account record types)

## Goal

The org has the demo cast from §19: two Loan Officers, a Credit Manager, a Credit Head, two Operations Officers and two portal borrowers. Each one has the right role, profile and permission set group, so every access rule can be shown by logging in as a real user. This is the M04 exit (AC-14) and later AC-06 and AC-13.

## Build

**Licence plan for the `Lams` org.** The org has 2 free full Salesforce licences, 6 Salesforce Platform, 1 Salesforce Integration and 5 Customer Community Login (the admin and the extra admin user "OrgFarm EPIC" already hold the other full licences, LAMS-002). The Platform licence has no Lead, Campaign or Case access, so the two full licences go to the staff who work Leads and Cases, and **the admin acts as the Credit Head** (no separate Credit Head user).

Usernames must be unique across all Salesforce orgs. Use a suffix such as `@lams-<yourinitials>.demo` (proposed). Use your own inbox for Email so notifications arrive. For every user: Locale *English (India)*, Time Zone *Asia/Kolkata*, Email Encoding UTF-8.

| User (proposed names) | Alias | Licence | Role | Profile | Assignment | Language |
| --- | --- | --- | --- | --- | --- | --- |
| You (existing System Administrator) – acts as Credit Head | – | Salesforce | Credit_Head | System Administrator | Group LAMS Credit Head + permission set **LAMS_Case_Access** (direct); **Marketing User** checkbox on (v2.2) | English |
| Priya Sharma – Loan Officer 1 | psharma | Salesforce | Loan_Officer | LAMS Internal User | Group LAMS Loan Officer + permission set **LAMS_Sales_Access** (direct); works Leads | English |
| Suresh Iyer – Operations Officer 1 | siyer | Salesforce | Operations_Officer | LAMS Internal User | Group LAMS Operations + permission set **LAMS_Case_Access** (direct); works Cases | English |
| Anita Desai – Credit Manager | adesai | Salesforce Platform | Credit_Manager | LAMS Internal Platform User (proposed) | Group LAMS Credit Manager | English |
| Rahul Verma – Loan Officer 2 | rverma | Salesforce Platform | Loan_Officer | LAMS Internal Platform User | Group LAMS Loan Officer; no Lead access | English |
| Meera Nair – Operations Officer 2 | mnair | Salesforce Platform | Operations_Officer | LAMS Internal Platform User | Group LAMS Operations; loans only, no Cases | English |
| Integration User | – | Salesforce Integration | – | Minimum Access - API Only Integrations | Created in LAMS-068 | – |
| Borrower 1 (Aarav Sharma, Contact ACC1 from LAMS-016) | – | Customer Community Login | – | LAMS Borrower | Permission set LAMS_Borrower_Portal | English |
| Borrower 2 (Priya Nair, Contact ACC2 from LAMS-016) | – | Customer Community Login | – | LAMS Borrower | Permission set LAMS_Borrower_Portal | **Hindi** (and Contact.Preferred_Language__c = Hindi, BR-54) |

- Set **Manager** on each Loan Officer to Anita Desai (proposed; useful for approval reminders and reports).
- **Marketing User** is a checkbox on the User record, not a permission. Without it the Credit Head (the admin) can't create or edit campaigns even with LAMS_Policy_Admin (§11, §19).
- **Testing as the admin proves nothing about security.** System Administrator has View All Data and Modify All Data, so sharing and most FLS limits don't apply to the Credit Head here. Prove the security ACs (AC-06, AC-13, AC-14) as the other users; Credit Head steps in approvals and settings are still run as the admin.
- **Licence-bound sets (BRD v2.3, Appendix D6):** Lead, Convert Leads and Campaign read are only in `LAMS_Sales_Access`, Case only in `LAMS_Case_Access` (LAMS-024). Assign them directly, never through a group, and only to full-licence users: Sales → Priya; Case → Suresh and the admin. The Platform users (Anita, Rahul, Meera) get their group only. Disputes route to the Credit Head queue (the admin) instead of the Credit Managers (LAMS-078), and the dynamic-dashboard demo compares Priya with Rahul (LAMS-081).
- The Accounts of the two borrower Contacts must be **owned by a user with a role**. Set the owner to Priya Sharma.
- The **Integration User** from §19 is created in LAMS-068 with its own licence.
- Queue memberships (Credit Head, Credit Managers, Operations) come in LAMS-048 and LAMS-078.

**Licences:** check Setup → Company Information → User Licenses against what you recorded in LAMS-002 (2 Salesforce and 6 Salesforce Platform free). If a licence is missing, drop Loan Officer 2 or Operations Officer 2 first (milestones README risk table: "Trim demo users"). Write down what you dropped.

**Script (proposed): `scripts/apex/create-test-users.apex`**. Anonymous Apex that:

1. Looks up the Profile, UserRole and PermissionSetGroup Ids by name (never hardcoded Ids).
2. Inserts the 5 staff users and the 2 portal users (`ContactId` from `SELECT Id FROM Contact WHERE PAN__c IN ('AAAPS1001A', 'AAAPN1002B')`). Use `Database.DMLOptions` with `EmailHeader.triggerUserEmail = false` so no welcome emails go out.
3. Updates the running admin user: `UserRoleId` = Credit_Head, `UserPermissionsMarketingUser = true`.
4. Inserts `PermissionSetAssignment` rows: `PermissionSetGroupId` for the groups (including LAMS Credit Head for the admin); `PermissionSetId` for LAMS_Sales_Access (Priya), LAMS_Case_Access (Suresh and the admin) and LAMS_Borrower_Portal (portal users). Look the sets up by `Name`, and assign the two access sets only to users whose `Profile.UserLicense.Name` is `Salesforce`; skip with a debug message otherwise.
5. Skips any user or assignment that already exists, so it is safe to re-run.

## Steps

1. Write the script, or create the users in Setup → Users and assign groups from each user's *Permission Set Group Assignments* related list and the two access sets from *Permission Set Assignments*.
2. Run it: `sf apex run --file scripts/apex/create-test-users.apex`.
3. Check: `sf data query --query "SELECT Username, Profile.Name, UserRole.Name, IsActive FROM User WHERE Username LIKE '%@lams-%'"` and `sf data query --query "SELECT Assignee.Username, PermissionSetGroup.DeveloperName, PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username LIKE '%@lams-%'"`.
4. Turn on Setup → Login Access Policies → *Administrators Can Log in as Any User*. Log in as each user once.
5. Run the AC-14 check from LAMS-027 as Suresh Iyer.
6. Commit the script: `chore(security): demo users and permission set group assignments [LAMS-029]`.

## Learn

- **Users can't be deleted**, only deactivated or frozen, and a used username can't be reused in any org. Pick usernames once.
- `sf org create user` works only for scratch orgs. In a Developer Edition, create users in Setup, by Apex or through the API.
- **Mixed DML:** User and PermissionSetAssignment are both setup objects, so they can share a transaction. Inserting a Contact or Account in the same transaction can't. Create the borrowers first (LAMS-016), then the portal users.
- `sf org assign permset` assigns permission sets, not permission set groups. For groups, use the UI or a `PermissionSetAssignment` with `PermissionSetGroupId`.
- **Tests and licences:** an Apex test that inserts a new Salesforce-licence user can fail with `LICENSE_LIMIT_EXCEEDED` when no full licence is free, which is the case in `Lams`. Tests that need a full-licence user (Lead or Case work) should run as an existing one: `TestDataFactory.loanOfficer()` (added in LAMS-095) returns the active user with a direct LAMS_Sales_Access assignment (Priya Sharma).

## Done when

- [ ] The 5 staff users exist with the licences, roles, profiles, groups and direct sets in the table (or the trimmed set, written down); the admin has the Credit_Head role, the LAMS Credit Head group, LAMS_Case_Access and Marketing User
- [ ] LAMS_Sales_Access is assigned only to Priya and LAMS_Case_Access only to Suresh and the admin; no Platform user holds either
- [ ] 2 portal users exist on LAMS Borrower with LAMS_Borrower_Portal; Borrower 2's language is Hindi
- [ ] Logged in as Priya, the LAMS app opens and she can create a Draft application and a Lead; as Anita, the Loan Product Edit button is missing; as the admin, it is present
- [ ] The admin can create a Campaign; Priya can open a Campaign but not edit it; Rahul, Anita and Meera have no Leads, Campaigns or Cases tab
- [ ] AC-14 passes logged in as Suresh Iyer (M04 exit criterion)
- [ ] The user script (if used) is committed under `scripts/apex/` and contains no hardcoded Ids
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Org setup checklist (users, Credit Head with Marketing User), §11 Profiles, Role hierarchy, Permission sets, Permission set groups, Appendix D6, §8 constraint C1, §9 AC-06, AC-13, AC-14, BR-54, BR-70, BR-88
