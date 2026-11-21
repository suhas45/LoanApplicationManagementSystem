# LAMS-031 · Loan_Application__c rules (10)

**Milestone:** [M05 – Validation rules](README.md) · **Size:** M (2–5h) · **Delivers:** §13.1

**Depends on:** M04 done; LAMS-009, LAMS-010, LAMS-011 (fields, roll-ups, Docs_Complete__c); LAMS-021 (labels)

## Goal

An application can't be saved with amounts or tenure outside the product, with terms changed after submission, or with a status it hasn't earned. A required reason or comment can't be skipped either. Whoever saves it (officer, borrower, partner API or automation) gets a clear, translatable message (BR-03, BR-08, BR-11, BR-15, BR-19, BR-23, BR-25, BR-26, BR-29, BR-32).

## Build

§13.1 lists 10 Loan_Application__c rows. Row 9 ("Rejection reason when Rejected; Withdrawal reason when Withdrawn") becomes **two** rules so each gets its own message, which makes **11 rules**.

| # | Rule name | Error location | Message = value of label | BR |
| --- | --- | --- | --- | --- |
| 1 | LA_Amount_Within_Product_Limits | Amount__c | LAMS_VR_Amount_Out_Of_Range | BR-03 |
| 2 | LA_Tenure_Within_Product_Limits | Tenure__c | LAMS_VR_Tenure_Out_Of_Range | BR-03 |
| 3 | LA_Terms_Locked_After_Draft | Top of page | LAMS_VR_Terms_Locked | BR-08 |
| 4 | LA_Approved_Amount_Not_Above_Amount | Approved_Amount__c | LAMS_VR_Approved_Amount_Too_High | BR-25 |
| 5 | LA_Under_Review_Needs_Docs | Top of page | LAMS_VR_Docs_Incomplete | BR-19 |
| 6 | LA_Approval_Needs_Score_And_Result | Top of page | LAMS_VR_Score_Eligibility_Required | BR-11 |
| 7 | LA_Override_Reason_Required | Override_Reason__c | LAMS_VR_Override_Reason_Required | BR-15 |
| 8 | LA_Comments_For_Refer_Or_Fail | Decision_Comments__c | LAMS_VR_Decision_Comments_Required | BR-23 |
| 9a | LA_Rejection_Reason_Required | Rejection_Reason__c | LAMS_VR_Rejection_Reason_Required | BR-26 |
| 9b | LA_Withdrawal_Reason_Required | Withdrawal_Reason__c | LAMS_VR_Withdrawal_Reason_Required | BR-32 |
| 10 | LA_Locked_After_Offer_Accepted | Top of page | LAMS_VR_Offer_Accepted_Locked | BR-29 |

Each rule is Active. Its **Description** starts with `Label: <label name>; BR-xx`, and its **Error Message** is the label's English value, copied exactly.

**Error condition formulas** (true = block the save):

```text
1  LA_Amount_Within_Product_Limits
AND(
  OR(ISNEW(), ISCHANGED(Amount__c), ISCHANGED(Loan_Product__c)),
  NOT(ISBLANK(Amount__c)),
  OR(Amount__c < Loan_Product__r.Min_Amount__c,
     Amount__c > Loan_Product__r.Max_Amount__c)
)

2  LA_Tenure_Within_Product_Limits
AND(
  OR(ISNEW(), ISCHANGED(Tenure__c), ISCHANGED(Loan_Product__c)),
  NOT(ISBLANK(Tenure__c)),
  OR(Tenure__c < Loan_Product__r.Min_Tenure__c,
     Tenure__c > Loan_Product__r.Max_Tenure__c)
)

3  LA_Terms_Locked_After_Draft
AND(
  NOT(ISNEW()),
  NOT(ISPICKVAL(PRIORVALUE(Status__c), "Draft")),
  OR(ISCHANGED(Loan_Product__c), ISCHANGED(Amount__c), ISCHANGED(Tenure__c))
)

4  LA_Approved_Amount_Not_Above_Amount
AND(
  NOT(ISBLANK(Approved_Amount__c)),
  Approved_Amount__c > Amount__c
)

5  LA_Under_Review_Needs_Docs
AND(
  ISPICKVAL(Status__c, "Under Review"),
  OR(ISNEW(), ISCHANGED(Status__c)),
  NOT(Docs_Complete__c)
)

6  LA_Approval_Needs_Score_And_Result
AND(
  ISPICKVAL(Status__c, "Approved"),
  OR(ISNEW(), ISCHANGED(Status__c)),
  OR(ISBLANK(Credit_Score__c), ISBLANK(TEXT(Eligibility_Result__c)))
)

7  LA_Override_Reason_Required
AND(
  ISPICKVAL(Credit_Score_Source__c, "Manual Override"),
  ISBLANK(Override_Reason__c)
)

8  LA_Comments_For_Refer_Or_Fail
AND(
  ISPICKVAL(Status__c, "Approved"),
  OR(ISNEW(), ISCHANGED(Status__c)),
  OR(ISPICKVAL(Eligibility_Result__c, "Refer"), ISPICKVAL(Eligibility_Result__c, "Fail")),
  ISBLANK(Decision_Comments__c)
)

9a LA_Rejection_Reason_Required
AND(
  ISPICKVAL(Status__c, "Rejected"),
  OR(ISNEW(), ISCHANGED(Status__c)),
  ISBLANK(TEXT(Rejection_Reason__c))
)

9b LA_Withdrawal_Reason_Required
AND(
  ISPICKVAL(Status__c, "Withdrawn"),
  OR(ISNEW(), ISCHANGED(Status__c)),
  ISBLANK(Withdrawal_Reason__c)
)

10 LA_Locked_After_Offer_Accepted
AND(
  NOT(ISNEW()),
  ISPICKVAL(Status__c, "Offer Accepted"),
  OR(ISCHANGED(Amount__c), ISCHANGED(Tenure__c), ISCHANGED(Approved_Amount__c))
)
```

Design choices:

- Rules 1 and 2 fire only when the amount, tenure or product changes. If the Credit Head later tightens a product's limits, old applications can still be saved.
- Rules 3 and 10 use the *prior* status (3) or the current one (10). The save that moves Draft → Submitted can still carry final edits, and Approved_Amount__c stays free until Offer Accepted, because approvers reduce it (BR-25).
- Status rules (5, 6, 8, 9a, 9b) fire only when the status **changes**. A roll-up recalculation or a later system update then can't fail on an old state.
- No rule depends on a toggle. If one ever must, read it with `$Setup.LAMS_Settings__c.<Field>`.
- No bypass permission (proposed). Automation must save valid data like everyone else.

**Hindi:** after deploying, translate each rule's error message in Translation Workbench (Setup Component *Validation Error Message*, object Loan Application) using the Hindi label values from LAMS-021.

## Steps

1. Create the rules in Object Manager → Loan Application → Validation Rules, or write `force-app/main/default/objects/Loan_Application__c/validationRules/<RuleName>.validationRule-meta.xml`:
   ```xml
   <ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
       <fullName>LA_Approved_Amount_Not_Above_Amount</fullName>
       <active>true</active>
       <description>Label: LAMS_VR_Approved_Amount_Too_High; BR-25</description>
       <errorConditionFormula>AND(NOT(ISBLANK(Approved_Amount__c)), Approved_Amount__c &gt; Amount__c)</errorConditionFormula>
       <errorDisplayField>Approved_Amount__c</errorDisplayField>
       <errorMessage>Approved amount can't be more than the requested amount.</errorMessage>
   </ValidationRule>
   ```
2. Deploy: `sf project deploy start --source-dir force-app/main/default/objects/Loan_Application__c/validationRules`.
3. Try each rule by hand once in the UI (a Draft PL application of ₹40,000 must fail rule 1).
4. Add the Hindi messages, then retrieve them: `sf project retrieve start --metadata CustomObject:Loan_Application__c CustomObjectTranslation:Loan_Application__c-hi`.
5. Commit: `feat(validation): Loan_Application__c validation rules with labels [LAMS-031]`.

## Learn

- **`ISNEW`, `ISCHANGED`, `PRIORVALUE`** make a rule fire on a *transition*, not on a state. That matters because roll-up summary changes make the parent record go through save again, validation rules included.
- **Picklists** need `ISPICKVAL()` or `TEXT()`. `ISBLANK(picklist)` doesn't compile.
- **Gotcha: approval process field updates don't run validation rules.** When Loan Approval (LAMS-048) sets Status = Approved or Rejected through a field update, rules 6, 8 and 9a don't fire. LAMS-048 must make the approver fill Decision_Comments__c and Rejection_Reason__c first (the record is editable by the approver). Apex and Flow updates are checked as normal.
- A validation rule's Error Message can't use `$Label`. The label is the source text, and the LAMS-033 tests assert `System.Label.X` against the actual message, so any drift fails CI.

## Done when

- [ ] 11 active rules exist with the names, formulas, error locations and messages above, in `force-app/`
- [ ] Each message matches its custom label's English value exactly, and has a Hindi translation in `objectTranslations/Loan_Application__c-hi/`
- [ ] By hand: a ₹40,000 Personal Loan fails rule 1; editing Amount on a Document Review application fails rule 3; setting Under Review with no verified documents fails rule 5
- [ ] The deploy succeeds; negative tests follow in LAMS-033
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §13.1 Validation rules, §10.3 Loan_Application__c, §13.4 Approval process, §12 (`$Setup` in validation rules), BR-03, BR-08, BR-11, BR-15, BR-19, BR-23, BR-25, BR-26, BR-29, BR-32, BR-54
