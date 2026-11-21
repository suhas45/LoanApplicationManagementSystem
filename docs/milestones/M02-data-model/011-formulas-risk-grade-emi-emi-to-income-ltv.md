# LAMS-011 · Formulas: Risk_Grade, EMI, EMI_To_Income, LTV

**Milestone:** [M02 – Data model](README.md) · **Size:** M (2–5h) · **Delivers:** BR-14, BR-39

**Depends on:** LAMS-009 (application fields), LAMS-008 (Contact income and existing EMI)

## Goal

The application calculates its own risk grade (BR-14), EMI by the reducing-balance formula rounded to ₹1 (BR-39), EMI-to-income and LTV. EligibilityService (LAMS-043) and approvers then read one consistent set of numbers, and AC-09 (₹1,00,000 at 14% for 12 months = ₹8,979) can be checked on a record.

## Build

All four are formula fields on `Loan_Application__c`, with *Treat blank fields as blanks*. In formulas a Percent field is a fraction: 14% is `0.14`, so the monthly rate is `rate / 12`, not `rate / 12 / 100`.

**Risk_Grade__c** — Formula (Text)

```
IF(ISBLANK(Credit_Score__c), "",
  IF(Credit_Score__c >= 780, "A",
  IF(Credit_Score__c >= 740, "B",
  IF(Credit_Score__c >= 700, "C",
  IF(Credit_Score__c >= 650, "D", "E")))))
```

**EMI__c** — Formula (Currency, 0 decimal places). Principal = Approved_Amount__c if set, else Amount__c. Rate = Interest_Rate__c if set, else the product's current rate (proposed: a draft has no copied rate yet, and without this the formula would show P ÷ n). Rate 0 → P ÷ n (§10.3).

```
IF(OR(ISBLANK(Tenure__c), Tenure__c <= 0), 0,
  IF(BLANKVALUE(Interest_Rate__c, Loan_Product__r.Interest_Rate__c) = 0,
    ROUND(BLANKVALUE(Approved_Amount__c, Amount__c) / Tenure__c, 0),
    ROUND(
      BLANKVALUE(Approved_Amount__c, Amount__c)
      * (BLANKVALUE(Interest_Rate__c, Loan_Product__r.Interest_Rate__c) / 12)
      * (1 + BLANKVALUE(Interest_Rate__c, Loan_Product__r.Interest_Rate__c) / 12) ^ Tenure__c
      / ((1 + BLANKVALUE(Interest_Rate__c, Loan_Product__r.Interest_Rate__c) / 12) ^ Tenure__c - 1),
    0)))
```

**EMI_To_Income__c** — Formula (Percent, 2 decimal places). (EMI + existing EMIs) ÷ monthly income; blank when income is missing or 0.

```
IF(OR(ISBLANK(Borrower__r.Monthly_Income__c), Borrower__r.Monthly_Income__c = 0), NULL,
  (EMI__c + BLANKVALUE(Borrower__r.Existing_EMI__c, 0)) / Borrower__r.Monthly_Income__c)
```

**LTV__c** — Formula (Percent, 2 decimal places). Amount ÷ property value (Home) or vehicle price (Auto); blank for products without either. Uses Approved_Amount__c when set (proposed, so a reduced amount re-scores LTV as BR-25 requires; §10.3 says only "Amount").

```
IF(BLANKVALUE(Property_Value__c, 0) > 0,
  BLANKVALUE(Approved_Amount__c, Amount__c) / Property_Value__c,
  IF(BLANKVALUE(Vehicle_Price__c, 0) > 0,
    BLANKVALUE(Approved_Amount__c, Amount__c) / Vehicle_Price__c,
    NULL))
```

Add help text to each field stating the rule and the BR ID. Put EMI, EMI-to-Income, LTV and Risk Grade on the application layout (read-only automatically).

**Worked checks**

| Case | Inputs | Expected |
| --- | --- | --- |
| AC-09 | PL product (14%), Amount 1,00,000, Tenure 12, no Interest_Rate__c yet | EMI__c = ₹8,979 |
| Approved amount wins | Same, Approved_Amount__c 80,000 | EMI__c = ₹7,183 |
| Zero rate | Interest_Rate__c 0, Amount 1,20,000, Tenure 12 | EMI__c = ₹10,000 |
| Home EMI | Interest_Rate__c 9%, Amount 60,00,000, Tenure 240 | EMI__c = ₹53,984 |
| Risk grade edges | Score 780 / 779 / 740 / 739 / 700 / 650 / 649 / blank | A / B / B / C / C / D / E / blank |
| EMI-to-income | EMI 8,979, Existing_EMI 5,000, income 50,000 | 27.96% |
| LTV | Home: Amount 40,00,000, Property 50,00,000 | 80.00% |

## Steps

1. Create the four fields in Object Manager with the formulas above; use *Check Syntax* and note the compiled size (limit 5,000 characters).
2. Add them to the layout.
3. Create test records for each row of the worked checks (use the PL and HL products from LAMS-007 or LAMS-016).
4. Retrieve:
   `sf project retrieve start --metadata CustomField:Loan_Application__c.Risk_Grade__c CustomField:Loan_Application__c.EMI__c CustomField:Loan_Application__c.EMI_To_Income__c CustomField:Loan_Application__c.LTV__c`
5. Commit: `feat(data-model): risk grade, EMI, EMI-to-income and LTV formulas [LAMS-011]`.

## Learn

- **Cross-object formulas** (`Loan_Product__r.…`, `Borrower__r.…`) read parent fields live; they count toward the 15 unique relationships per object.
- **Percent arithmetic:** formulas see fractions, the UI and the API show whole numbers (14), and Apex reads 14 from the field. The emiCalculator LWC (LAMS-034) and EmiScheduleService (LAMS-055) must use the same rounding as this formula (`ROUND(x, 0)`, half up).
- **Formula fields recalculate on read**, so they cannot be tracked in field history or trusted as record-triggered flow entry conditions.
- Repeating a sub-expression grows the compiled size; if you hit the limit, move the rate into its own helper formula field.

## Done when

- [ ] The four formula fields exist in the org and in source
- [ ] Every row of the worked-checks table gives the expected value on a real record
- [ ] AC-09: the ₹1,00,000 / 12 months / PL record shows EMI ₹8,979 (M02 exit criterion)
- [ ] BRD §10.3 updated: EMI__c falls back to the product rate before submit; LTV__c uses Approved_Amount__c when set
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §10.3 (Risk_Grade__c, EMI__c, EMI_To_Income__c, LTV__c), §10.6 EMI formula; §21 Formula fields; BR-11, BR-14, BR-25, BR-39; AC-09
