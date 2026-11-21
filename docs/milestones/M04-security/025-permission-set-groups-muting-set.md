# LAMS-025 · Permission set groups + muting set

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-74

**Depends on:** LAMS-024

## Goal

Each staff job is one permission set group, so a user gets one assignment instead of three or four. A muting set takes product editing away from Credit Managers, so only the Credit Head changes products and settings (BR-74). Credit Managers still share the LAMS_Credit set with the Credit Head.

## Build

| Group label | API name (proposed) | Permission sets | Muting set |
| --- | --- | --- | --- |
| LAMS Loan Officer | LAMS_Loan_Officer_Group | LAMS_Loan_Officer, LAMS_Reports, LAMS_Agentforce_User | – |
| LAMS Credit Manager | LAMS_Credit_Manager_Group | LAMS_Credit, LAMS_Reports, LAMS_Agentforce_User | LAMS_Credit_Manager_Muting |
| LAMS Credit Head | LAMS_Credit_Head_Group | LAMS_Credit, LAMS_Policy_Admin, LAMS_Reports, LAMS_Agentforce_User | – |
| LAMS Operations | LAMS_Operations_Group | LAMS_Operations, LAMS_Reports | – |

The `_Group` suffix keeps the group API names distinct from the permission sets they contain.

**Muting permission set `LAMS_Credit_Manager_Muting`** (lives inside LAMS Credit Manager):

| Object | Muted |
| --- | --- |
| Loan_Product__c | Create, Edit |
| Product_Document__c | Create, Edit, Delete (proposed: the checklist is part of the product) |

Nothing else is muted. LAMS_Override_Credit_Check and LAMS_Waive_Late_Fee stay with Credit Managers (BR-15, BR-51).

LAMS_Borrower_Portal and LAMS_Integration are not in any group. They are assigned directly to portal users and the Integration User.

## Steps

1. Setup → Permission Set Groups → New, for each of the 4 groups. Add the permission sets.
2. In *LAMS Credit Manager* → Muting Permission Set → New `LAMS_Credit_Manager_Muting`. Then Object Settings → Loan Product → tick Create and Edit under *Muted*. Do the same for Product Document.
3. Wait until each group's **Status** is *Updated*, not *Outdated* or *Failed*. Open **View Summary** on *LAMS Credit Manager* and check that Loan Product shows Read only.
4. Retrieve: `sf project retrieve start --metadata PermissionSetGroup:LAMS_Loan_Officer_Group PermissionSetGroup:LAMS_Credit_Manager_Group PermissionSetGroup:LAMS_Credit_Head_Group PermissionSetGroup:LAMS_Operations_Group MutingPermissionSet:LAMS_Credit_Manager_Muting`
5. Commit: `feat(security): permission set groups and Credit Manager muting set [LAMS-025]`.

## Learn

- **Muting only subtracts, and only inside its own group.** It removes a permission even though LAMS_Credit grants it, without forking LAMS_Credit into two near-copies.
- **Group recalculation is asynchronous.** After any change to a member permission set, the group shows *Outdated* until it recalculates. A deploy that includes groups can finish before they are *Updated*.
- In Apex tests, assign a group with a `PermissionSetAssignment` (`PermissionSetGroupId`). Then call `Test.calculatePermissionSetGroup(groupId)` before `System.runAs`, or the user won't have the group's permissions yet.
- Deploy order: permission sets → muting set → groups. A group can't reference a set that doesn't exist.

## Done when

- [ ] 4 groups and 1 muting set exist with the members above, all with Status *Updated*
- [ ] View Summary of LAMS Credit Manager shows Loan_Product__c Read only; LAMS Credit Head shows Read/Create/Edit
- [ ] Group and muting files are in `force-app/main/default/permissionsetgroups/` and `mutingpermissionsets/` and deploy cleanly
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Permission set groups and Permission sets, §21 (Profiles, permission sets, groups, muting), BR-15, BR-51, BR-74
