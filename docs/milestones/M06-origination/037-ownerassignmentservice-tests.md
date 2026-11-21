# LAMS-037 · OwnerAssignmentService + tests

**Milestone:** [M06 – Origination](README.md) · **Size:** M (2–5h) · **Delivers:** BR-07, BR-33

**Depends on:** LAMS-022 (roles Loan Officer, Operations Officer), LAMS-009 (Loan_Application__c), LAMS-012 (Loan__c.Assigned_Officer__c), LAMS-029 (test users, for the manual check)

## Goal

Portal and partner applications are given to the active Loan Officer with the fewest open applications at submission (BR-07), so they become visible to that officer and their Credit Manager through the role hierarchy. New loans get an Operations Officer the same way (BR-33, used by LAMS-053).

## Build

**Class `OwnerAssignmentService`** — `public without sharing class` (it must count every officer's records, not only the ones the running user can see; say so in a class comment).

```apex
public class Request {
    @InvocableVariable(required=true label='Mode' description='Application | Loan')
    public String mode;
    @InvocableVariable(required=true label='Record Id') public Id recordId;
}
public class Result {
    @InvocableVariable(label='Assigned User Id') public Id assignedUserId;
}

@InvocableMethod(label='Assign Officer' category='LAMS'
    description='mode Application → Loan Officer; mode Loan → Operations Officer')
public static List<Result> assign(List<Request> requests);

public static Map<Id, Id> assignLoanOfficers(List<Id> applicationIds);   // appId → userId
public static Map<Id, Id> assignOperationsOfficers(List<Id> loanIds);    // loanId → userId
```

A class can hold only one `@InvocableMethod`, so one action serves both objects through the `mode` input: `'Application'` (Application Submitted flow, LAMS-038) or `'Loan'` (Offer Accepted flow, LAMS-053). Any other value, or a recordId whose object does not match the mode, throws `IllegalArgumentException`. Results come back in the same order as the requests.

**Algorithm (both branches)**

| Step | Loan Officer branch | Operations Officer branch |
| --- | --- | --- |
| Candidates | `User` where `IsActive = true` and `UserRole.DeveloperName = 'Loan_Officer'` | same with `'Operations_Officer'` |
| Open work | `SELECT OwnerId, COUNT(Id) FROM Loan_Application__c WHERE Status__c IN :OPEN_STATUSES AND OwnerId IN :candidates GROUP BY OwnerId` | `SELECT Assigned_Officer__c, COUNT(Id) FROM Loan__c WHERE Status__c IN ('Pending Disbursement','Active') AND Assigned_Officer__c IN :candidates GROUP BY Assigned_Officer__c` |
| Pick | Lowest count; tie → lowest User Id (deterministic) | same |
| Bulk | After each pick add 1 to that user's count in memory, so 200 records spread evenly instead of all going to one person | same |

- `OPEN_STATUSES` = Submitted, Document Review, Under Review (proposed definition of "open").
- Role developer names come from LAMS-022; keep them in constants, not inline.
- No DML: the service returns the user Id and the calling flow writes OwnerId / Assigned_Officer__c in its own update (one DML in the flow).
- No candidate found → `assignedUserId = null` and a `System.debug(LoggingLevel.ERROR, …)`; the flow keeps the current owner.
- Two SOQL queries per branch regardless of record count.

## Steps

1. `sf apex generate class --name OwnerAssignmentService --output-dir force-app/main/default/classes` and `OwnerAssignmentServiceTest`.
2. Write the service; build test users in the test with `UserRole` lookups by DeveloperName (create users inside `System.runAs(admin)` to avoid mixed-DML errors).
3. `sf project deploy start --source-dir force-app/main/default/classes`
4. `sf apex run test --class-names OwnerAssignmentServiceTest --code-coverage --result-format human --wait 10`
5. Commit: `feat(apex): OwnerAssignmentService least-loaded assignment [LAMS-037]`.

## Learn

- **Why not a queue:** role hierarchy opens records owned by users below a manager, but not records owned by a queue (§11). Giving the record to a real Loan Officer is what makes the Credit Manager see it.
- **Invocable contract:** one `@InvocableMethod` per class; Flow sends all interviews in one list and expects one result per request, in order.
- **`without sharing` on purpose:** a service that balances workload must see all work; document the reason so a reviewer does not "fix" it.
- **Mixed DML:** inserting Users (setup objects) and business records in one test transaction fails unless separated with `System.runAs`.

## Done when

- [ ] Officer A has 3 open applications, officer B has 1 → the next application goes to B
- [ ] 200 applications with two idle officers → 100 each
- [ ] Inactive officers and users in other roles are never picked
- [ ] Draft, Approved, Rejected and other closed statuses are not counted as open
- [ ] Loan__c records get the Operations Officer with the fewest Pending Disbursement + Active loans
- [ ] A mixed request (mode Application and mode Loan rows) returns the right user per row, in request order; an unknown mode or a mode/object mismatch throws
- [ ] No candidate → null result, no exception
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-07, BR-33, BR-70, §11 Owner assignment and role hierarchy, §14 OwnerAssignmentService, NFR-01
