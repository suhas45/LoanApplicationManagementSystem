# LAMS-022 · Role hierarchy

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** §11

**Depends on:** M03 done

## Goal

Four roles mirror the lender's reporting lines: Credit Head → Credit Manager → Loan Officer, and Credit Head → Operations Officer. With Private OWDs, managers automatically see their team's applications (BR-70, AC-06), and the criteria sharing rule (LAMS-026) has an Operations role to share with.

## Build

| Role label | DeveloperName (proposed) | Reports to | Sees records of |
| --- | --- | --- | --- |
| Credit Head | Credit_Head | – (top of the LAMS tree) | Everyone below |
| Credit Manager | Credit_Manager | Credit_Head | Loan Officers |
| Loan Officer | Loan_Officer | Credit_Manager | Own records only |
| Operations Officer | Operations_Officer | Credit_Head | Own records only |

- Leave the role access settings for Account, Case and Opportunity at their defaults ("can't access" / "view only" where offered). Contact has no role option: Contact sharing is Controlled by Parent (LAMS-026), so Contact access follows the Account. Access to LAMS data comes from OWDs, sharing and permission sets, not from these options.
- Keep **Grant Access Using Hierarchies** on for every LAMS custom object. It is on by default. Don't untick it in LAMS-026.
- In the `Lams` org the **Credit Head role is held by the System Administrator** (the developer), because only 2 full licences are free (LAMS-029). Give your admin user the Credit_Head role once it exists.
- Portal borrowers get no internal role. Customer Community Login users have no role hierarchy, and their access comes from the sharing set (LAMS-077).
- One team is enough for the demo (§19: 1 Credit Manager). If a second Credit Manager is added, give each team its own pair of roles (for example `Credit_Manager_North` → `Loan_Officer_North`). Otherwise both managers see both teams, which breaks BR-62 "their own team" (proposed).

## Steps

1. Setup → Roles → Set Up Roles → Add Role, top-down: Credit Head, then Credit Manager and Operations Officer under it, then Loan Officer under Credit Manager.
2. Retrieve: `sf project retrieve start --metadata Role:Credit_Head Role:Credit_Manager Role:Loan_Officer Role:Operations_Officer`. Files land in `force-app/main/default/roles/`.
3. Check that `parentRole` in each `.role-meta.xml` matches the table.
4. Commit: `feat(security): LAMS role hierarchy [LAMS-022]`.

## Learn

- **Roles open records upward:** a manager gets the same access as their subordinates to records those subordinates own *or have been shared*. That includes Apex managed shares on Loan__c (LAMS-054), so the Credit Head also sees Operations' loans.
- **Roles are not permissions.** A role decides which *records* a user sees. Profiles and permission sets decide which *objects and fields*.
- **Gotcha for the portal (M10):** the owner of a portal borrower's Account (their Individual Borrower Account, or the business Account of a director) must have a role, or the portal user can't be created. Have a Loan Officer own the borrower Accounts in seed data or self-registration.
- Deploying roles is safe, but deleting a role that users hold fails. Reassign the users first.

## Done when

- [ ] Setup → Roles shows Credit Head at the top with Credit Manager → Loan Officer and Operations Officer beneath it
- [ ] The 4 `.role-meta.xml` files are in `force-app/main/default/roles/` and deploy cleanly
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Role hierarchy and Sharing, §4 Users, personas and roles, §19 users list, BR-62, BR-70, AC-06
