# LAMS-054 · LoanTrigger + LoanSharingService + tests

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-70

**Depends on:** LAMS-012 (Loan__c, Assigned_Officer__c), LAMS-026 (Loan__c OWD Private), LAMS-029 (two Operations Officer test users), LAMS-053 (loans are created with an assigned officer)

## Goal

Each Operations Officer can read and edit only the loans assigned to them. When a loan is reassigned, the previous officer loses access (BR-70). Access is granted with Apex managed sharing, reason `Assigned_Officer`.

## Build

**Apex sharing reason** on `Loan__c`: Label *Assigned Officer*, Name `Assigned_Officer`. Apex refers to it as `Schema.Loan__Share.RowCause.Assigned_Officer__c`. Metadata type: `SharingReason` `Loan__c.Assigned_Officer`.

**Trigger `LoanTrigger`** — `trigger LoanTrigger on Loan__c (after insert, after update)`. The trigger holds no logic; it calls `LoanTriggerHandler` (proposed name). This is the only trigger on Loan__c (NFR-09), and later items add their logic to the handler.

| Class | Signature | Does |
| --- | --- | --- |
| `LoanTriggerHandler` | `public static void afterInsert(List<Loan__c> newList)` / `afterUpdate(Map<Id, Loan__c> newMap, Map<Id, Loan__c> oldMap)` | Routes to LoanSharingService |
| `LoanSharingService` | `public without sharing class` | Owns all `Loan__Share` rows with reason Assigned_Officer |
| | `public static void syncShares(List<Loan__c> loans, Map<Id, Loan__c> oldMap)` | `oldMap` is null on insert |

`syncShares` algorithm:

1. Pick the loans to process. On insert: `Assigned_Officer__c` is not null. On update: `Assigned_Officer__c` changed, or `OwnerId` changed (the officer may now be the owner).
2. Delete existing shares: a single query, `SELECT Id FROM Loan__Share WHERE ParentId IN :ids AND RowCause = :Schema.Loan__Share.RowCause.Assigned_Officer__c`, then delete the results.
3. Build new shares for each loan where the officer is not null and the officer ≠ `OwnerId` (the owner already has full access):
   `new Loan__Share(ParentId = loan.Id, UserOrGroupId = loan.Assigned_Officer__c, AccessLevel = 'Edit', RowCause = Schema.Loan__Share.RowCause.Assigned_Officer__c)`
4. `Database.insert(shares, false)`. For each failure (for example an inactive user), call `addError` on the matching trigger record with custom label `LAMS_Loan_Share_Failed` (proposed) plus the error message. The transaction then rolls back and the user sees why.
5. No toggle applies. Sharing is always on.

Run as `without sharing`: the running user (an Operations Officer saving a reassignment, or the Automated Process user) is not the owner and may not have rights to create share rows.

## Steps

1. Create the sharing reason: Setup → Object Manager → Loan → Apex Sharing Reasons → New. The option appears only when the Loan OWD is Private (LAMS-026).
2. Write `LoanSharingService`, `LoanTriggerHandler` and `LoanTrigger`.
3. Write `LoanSharingServiceTest`. Create the users inside the test, or query the LAMS-029 users by username and assign the LAMS Operations group in the test:
   - insert a loan for officer A → one share, AccessLevel Edit, RowCause Assigned_Officer
   - reassign to B → A's share gone, B's present
   - clear the officer → no Assigned_Officer shares
   - officer = owner → no share row, no error
   - `System.runAs(A)`: `[SELECT Id FROM Loan__c]` returns A's loan; `System.runAs(B)` returns none
   - bulk: 200 loans alternating A/B in one insert, then reassign all 200 in one update → 200 shares, 2 queries and 2 DML statements in the service (assert with `Limits.getQueries()`)
4. Deploy and test: `sf project deploy start --source-dir force-app/main/default/classes --source-dir force-app/main/default/triggers --source-dir force-app/main/default/objects/Loan__c` then `sf apex run test --class-names LoanSharingServiceTest --code-coverage --result-format human --wait 10`
5. Retrieve the sharing reason: `sf project retrieve start --metadata SharingReason:Loan__c.Assigned_Officer`
6. Commit: `feat(security): LoanTrigger and LoanSharingService with Assigned_Officer reason [LAMS-054]`.

## Learn

- **Apex managed sharing needs OWD Private (or Public Read Only) and a custom sharing reason.** Shares with a custom RowCause survive owner changes. Manual shares (`RowCause = Manual`) are deleted when the owner changes.
- **Share objects:** a custom object `X__c` gets `X__Share` with ParentId, UserOrGroupId, AccessLevel (`Read`/`Edit`) and RowCause. Inserting a share for the record owner is not needed and can fail.
- `with sharing` decides which records your SOQL sees. It does not give the right to manage shares, so service classes that write shares usually run `without sharing`.
- An optional Apex sharing recalculation class (`Database.Batchable` registered on the sharing reason) rebuilds shares if they ever drift. This is useful at go-live, but not required here.

## Done when

- [ ] Sharing reason `Assigned_Officer` exists on Loan__c and in source
- [ ] Logged in as Operations Officer A, the loan assigned to A opens and is editable; a loan assigned to B is not found (list view and URL)
- [ ] Reassigning a loan from A to B removes A's access immediately
- [ ] The Loan__c record shows the officer in Sharing Hierarchy / "Sharing" with reason Assigned Officer
- [ ] `LoanSharingServiceTest` passes, including the 200-record insert and reassign, with ≥ 90% coverage for LoanSharingService and LoanTriggerHandler
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.14 BR-70, §10.5 Assigned_Officer__c, §11 Sharing (Apex managed sharing, reason Assigned_Officer), §14 LoanTrigger + LoanSharingService, NFR-01, NFR-09
