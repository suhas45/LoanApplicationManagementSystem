# LAMS-043 · EligibilityService (Pass/Refer/Fail) + tests

**Milestone:** [M06 – Origination](README.md) · **Size:** L (5–10h) · **Delivers:** BR-11, BR-12

**Depends on:** LAMS-041 (score on the record), LAMS-011 (EMI_To_Income__c, LTV__c, Risk_Grade__c formulas), LAMS-008 (Contact Birthdate, Monthly_Income__c, Existing_EMI__c, KYC_Status__c), LAMS-017 / LAMS-019 (Refer tolerances through FeatureToggle). Must be done before LAMS-042, which calls it.

## Goal

Apply the product's credit policy the same way every time (O2): run the five rules only once a credit score exists (BR-11, AC-04), return Pass, Refer or Fail with each breach listed (BR-12), and force Fail when KYC is Rejected (BR-13).

## Build

**Class `EligibilityService`** — `public without sharing class` (called from KycService running as the submitter and from the Override Credit Score flow; it must read the borrower and product whatever the caller's sharing).

```apex
public class Request {
    @InvocableVariable(required=true label='Application Id') public Id applicationId;
}
public class Result {
    @InvocableVariable public String eligibilityResult;   // Pass | Refer | Fail | Skipped
    @InvocableVariable public String eligibilityNotes;
}

@InvocableMethod(label='Run Eligibility' category='LAMS')
public static List<Result> run(List<Request> requests);

public static Map<Id, String> evaluate(Set<Id> applicationIds);   // for Apex callers (KycService)

@TestVisible
static Outcome check(Loan_Application__c app, Contact borrower, Loan_Product__c product,
                     Decimal scoreTolerance, Decimal ratioTolerance);   // pure logic, no SOQL/DML
```

**Guard:** an application with `Credit_Score__c = null` is not evaluated — result `Skipped`, no fields written, Eligibility_Run_Date__c stays blank (BR-11, AC-04).

**Rules** (all limits from Loan_Product__c; tolerances from LAMS_Settings__c via FeatureToggle)

| Rule | Value checked | Breach | Soft (→ Refer) when | Otherwise |
| --- | --- | --- | --- | --- |
| Age at maturity | Whole years from Borrower Birthdate to `Submitted_Date__c` (or today) + Tenure__c months | > Max_Age_At_Maturity__c, or Birthdate blank | never | Hard |
| Minimum income | Borrower Monthly_Income__c | < Min_Monthly_Income__c, or blank | never | Hard |
| Minimum score | Credit_Score__c | < Min_Credit_Score__c | shortfall ≤ Refer_Score_Tolerance__c (20) | Hard |
| EMI-to-income | EMI_To_Income__c (includes Existing_EMI__c) | > Max_EMI_To_Income__c, or blank | excess ≤ Refer_Ratio_Tolerance__c (5 points) | Hard |
| LTV | LTV__c — only when product Max_LTV__c is not blank | > Max_LTV__c, or LTV__c blank (no property value / vehicle price) | excess ≤ Refer_Ratio_Tolerance__c | Hard |
| KYC | Borrower KYC_Status__c | = Rejected | never | Fail regardless of the rest (BR-13) |

**Result:** any hard breach or KYC Rejected → **Fail**; else any soft breach → **Refer**; else **Pass**. Values equal to the limit pass (≥ minimum, ≤ maximum).

**Writes (one update for all records):** Eligibility_Result__c, Eligibility_Notes__c (one line per breach, newest run replaces the old text), Eligibility_Run_Date__c = now. EMI__c already uses Approved_Amount__c when set, so re-running after an approver reduces the amount re-checks the lower EMI (BR-25).

**Notes text** — custom labels with `String.format` placeholders (proposed names): `LAMS_Elig_Age` ("Age at maturity {0} exceeds {1}"), `LAMS_Elig_Income`, `LAMS_Elig_Score` ("Credit score {0} below minimum {1} ({2})"), `LAMS_Elig_EMI_Ratio`, `LAMS_Elig_LTV`, `LAMS_Elig_KYC_Rejected`, `LAMS_Elig_Soft`, `LAMS_Elig_Hard`.

**Queries:** one query for applications with `Borrower__r` and `Loan_Product__r` fields; tolerances read once per call. No SOQL or DML in loops.

## Steps

1. `sf apex generate class --name EligibilityService --output-dir force-app/main/default/classes` and `EligibilityServiceTest`.
2. Write `check()` first and test it with in-memory records: build the application, then `Formula.recalculateFormulas(new List<SObject>{ app })` to evaluate EMI_To_Income__c and LTV__c without DML.
3. Add `evaluate()` and the invocable around it; then DML tests through TestDataFactory.
4. `sf project deploy start --source-dir force-app/main/default/classes`
5. `sf apex run test --class-names EligibilityServiceTest --code-coverage --result-format human --wait 10`
6. Commit: `feat(apex): EligibilityService with Pass/Refer/Fail and tolerances [LAMS-043]`.

## Learn

- **Separate rules from data access:** a pure `check()` method is fast to test at every boundary; the SOQL/DML wrapper is tested once for bulk.
- **`Formula.recalculateFormulas`** evaluates formula fields (including cross-object ones loaded in memory) without saving.
- **Percent fields in Apex** hold the number shown (50 means 50%), so tolerances in points add directly.
- **Why the guard matters:** in v1 eligibility ran before the score existed and the score rule could never pass; refusing to run without a score is what AC-04 checks.

## Done when

- [ ] PL, score 790, income 60,000, ratio 30%, age fine → Pass, notes empty, Eligibility_Run_Date__c set
- [ ] Score exactly at minimum (700) → Pass; 680 (20 below) → Refer; 679 → Fail
- [ ] EMI-to-income 55% on a 50% product → Refer; 55.01% → Fail; LTV 85% on Home (80%) → Refer; 86% → Fail; LTV ignored on PL and BL (Max_LTV__c blank)
- [ ] Age at maturity over the limit, income below minimum, Birthdate blank → Fail with a note each
- [ ] KYC Rejected with everything else passing → Fail (BR-13)
- [ ] Several breaches → every one listed in Eligibility_Notes__c
- [ ] Credit_Score__c blank → Skipped, nothing written (AC-04 guard)
- [ ] Tolerance setting changed to 0 → 690 on a 700 product becomes Fail (setting read, not hardcoded)
- [ ] Bulk: 200 applications evaluated in one call with 1 SOQL and 1 DML; invocable returns 200 results in request order
- [ ] Coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-11, BR-12, BR-13, BR-14, BR-25, §5 product rules, §10.2, §10.3 EMI\_To\_Income\_\_c, LTV\_\_c, Eligibility fields, §12 Refer\_Score\_Tolerance\_\_c, Refer\_Ratio\_Tolerance\_\_c, §14 EligibilityService, AC-04
