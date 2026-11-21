# LAMS-033 · Negative tests for every rule

**Milestone:** [M05 – Validation rules](README.md) · **Size:** S (≤ 2h) · **Delivers:** NFR-10

**Depends on:** LAMS-031, LAMS-032

## Goal

Each of the 16 validation rules has an Apex test that tries to save an invalid record and asserts the exact custom-label message, plus a valid counterpart that saves. A rule that is deactivated, loosened or reworded then fails CI (NFR-10, M05 exit criterion). The shared `TestDataFactory` that later tests reuse also starts here (§14 Tests).

## Build

**`TestDataFactory`** (`@IsTest public class`; create it here if it doesn't exist yet). Methods return records **not inserted** unless the name says `create`:

| Method | Returns |
| --- | --- |
| `createProduct(String code)` | Inserted Loan_Product__c with the §5 seed values for PL, HL, AL or BL |
| `createBorrower(String pan)` | Inserted Account + Contact (PAN__c, Birthdate, Monthly_Income__c, KYC_Status__c = Verified) |
| `newApplication(Loan_Product__c p, Contact b, Decimal amount, Integer tenure, String status)` | Loan_Application__c with the matching record type |
| `createDocument(Loan_Application__c a, Boolean mandatory, String status)` | Inserted Application_Document__c |
| `createLoan(Loan_Application__c a)` | Inserted Loan__c (Application_Key__c = a.Id, Status Pending Disbursement) |
| `newInstalment(Loan__c l, Integer no)` / `newPayment(Loan__c l, Decimal amount, String reference)` | Child records |
| `createUser(String profileName, String groupOrPermSetName)` | Inserted user with the group or permission set assigned |

**Test classes and the rule each method covers**

`LoanApplicationValidationTest`

| Rule | Negative test (expect failure + label) | Positive control (expect success) |
| --- | --- | --- |
| LA_Amount_Within_Product_Limits | PL at ₹40,000 → `LAMS_VR_Amount_Out_Of_Range`; also ₹11,00,000 | PL at ₹3,00,000 |
| LA_Tenure_Within_Product_Limits | PL at 6 months → `LAMS_VR_Tenure_Out_Of_Range`; also 72 | PL at 24 months |
| LA_Terms_Locked_After_Draft | Document Review app, change Amount__c → `LAMS_VR_Terms_Locked` | Draft app, change Amount__c |
| LA_Approved_Amount_Not_Above_Amount | Amount 3,00,000, Approved 3,50,000 → `LAMS_VR_Approved_Amount_Too_High` | Approved 2,50,000 |
| LA_Under_Review_Needs_Docs | Document Review, no docs → Under Review → `LAMS_VR_Docs_Incomplete` | With 1 mandatory Verified doc |
| LA_Approval_Needs_Score_And_Result | Document Review, no score → Approved → `LAMS_VR_Score_Eligibility_Required` | Score 790 + Pass |
| LA_Override_Reason_Required | Source Manual Override, no reason → `LAMS_VR_Override_Reason_Required` | With reason |
| LA_Comments_For_Refer_Or_Fail | Refer, no comments → Approved → `LAMS_VR_Decision_Comments_Required`; same for Fail | Refer with comments |
| LA_Rejection_Reason_Required | → Rejected without reason → `LAMS_VR_Rejection_Reason_Required` | With reason Policy |
| LA_Withdrawal_Reason_Required | → Withdrawn without reason → `LAMS_VR_Withdrawal_Reason_Required` | With reason |
| LA_Locked_After_Offer_Accepted | Offer Accepted, change Approved_Amount__c → `LAMS_VR_Offer_Accepted_Locked` | Change Decision_Comments__c |
| Bulk | 200 PL applications at ₹40,000 with `Database.insert(list, false)` → 200 failures, each with the label | – |

`ServicingValidationTest`

| Rule | Negative test | Positive control |
| --- | --- | --- |
| AD_Rejection_Reason_Required | Doc → Rejected without reason → `LAMS_VR_Doc_Rejection_Reason_Required` | With reason |
| EMI_Waiver_Reason_Required | Waived, no reason (as a user with the permission) → `LAMS_VR_Waiver_Reason_Required` | With reason |
| EMI_Waiver_Needs_Permission | `System.runAs` a LAMS Operations user → tick Late_Fee_Waived__c → `LAMS_VR_Waiver_Not_Permitted` | `runAs` a LAMS Credit Manager user (group + `Test.calculatePermissionSetGroup`) |
| PAY_Amount_Positive | Amount 0 → `LAMS_VR_Payment_Amount_Positive`; also −100 | Amount 8,979 |
| PAY_Locked_After_Insert | Change Amount__c, Reference__c, Payment_Date__c or Mode__c → `LAMS_VR_Payment_Locked` | Status → Reversed with Reversal_Reason__c |

**Assertion pattern** (one method per row, named `<rule>_fails` / `<rule>_passes`):

```apex
Database.SaveResult sr = Database.update(app, false);
Assert.isFalse(sr.isSuccess(), 'rule should block the save');
Assert.areEqual(System.Label.LAMS_VR_Terms_Locked, sr.getErrors()[0].getMessage());
```

For the waiver tests, set the test Loan's `OwnerId` to the `runAs` user. Record access then can't be the reason a save fails, and only the rule is tested.

Insert records **directly in the prior status** (for example Document Review) rather than walking through Submitted. That way the Application Submitted automation from LAMS-038 and its callouts never run in these tests. Seed `LAMS_Settings__c` with the §12 defaults in `@TestSetup`, because later flows read `$Setup`.

## Steps

1. `sf apex generate class --name TestDataFactory --output-dir force-app/main/default/classes`, then `LoanApplicationValidationTest` and `ServicingValidationTest`.
2. Write a `_fails` and a `_passes` method for every row, plus the bulk test.
3. Deploy and run: `sf apex run test --class-names LoanApplicationValidationTest --class-names ServicingValidationTest --result-format human --wait 10`.
4. Prove a test catches drift: deactivate one rule in the org, re-run, see the test fail, then reactivate it.
5. Commit: `test(validation): negative and positive tests for all 16 rules [LAMS-033]`.

## Learn

- **`Database.insert/update(records, false)`** returns per-record errors instead of throwing, which suits bulk and negative tests. `try { update x; Assert.fail(); } catch (DmlException e)` is the single-record alternative.
- **Validation rules don't count toward Apex coverage**, and neither do `@IsTest` classes like TestDataFactory. These tests guard behaviour, not the coverage number.
- **Running user matters:** `$Permission` and the label language follow the user in `System.runAs`. Run the tests as an English-language user, or `System.Label` and the message both come back in Hindi. They still match, but the failures are harder to read.
- **Plan for later automation:** if a later item adds a trigger or flow that breaks these tests, give the tests the mocks or toggles they need (for example `Event_Publishing_Enabled__c = false`). Don't weaken the assertions.

## Done when

- [ ] Every rule from LAMS-031 (11) and LAMS-032 (5) has at least one failing-save test that asserts its `System.Label` message, and one passing counterpart
- [ ] The 200-record bulk test passes
- [ ] Both test classes pass locally and in CI (`RunLocalTests`)
- [ ] TestDataFactory is committed and has no hardcoded Ids
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §13.1 Validation rules, §14 Tests (TestDataFactory, bulk 200), §5 product seed values, §20 step 5 done-check, NFR-01, NFR-10
