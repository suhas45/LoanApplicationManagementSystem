# LAMS-034 · emiCalculator LWC + Jest tests

**Milestone:** [M06 – Origination](README.md) · **Size:** M (2–5h) · **Delivers:** BR-04

**Depends on:** LAMS-007 (Loan_Product__c), LAMS-011 (EMI__c formula the component must match), LAMS-015 (LAMS app and utility bar), LAMS-021 (custom labels)

## Goal

Show the estimated EMI live, without a server round trip, while the amount and tenure are being entered (BR-04, NFR-02: under 1 second). The same component is reused on the application page, in the utility bar, on the portal home page and inside the New Loan Application flow (LAMS-035).

## Build

**LWC `emiCalculator`** (`force-app/main/default/lwc/emiCalculator/`)

| File | Contents |
| --- | --- |
| `emiCalculator.js` | Component class |
| `emiMath.js` | Pure function `export function calculateEmi(principal, annualRate, months)` so Jest (and later emiSchedule, LAMS-057) can import it |
| `emiCalculator.html` | Amount and tenure inputs (`lightning-input` type number + `lightning-slider`), product picker, EMI, total interest, total payable |
| `emiCalculator.js-meta.xml` | Targets and flow properties below |
| `__tests__/emiCalculator.test.js`, `__tests__/emiMath.test.js` | Jest tests |

**EMI formula** (same as EMI__c, §10.6): r = annualRate ÷ 12 ÷ 100, n = months. If r = 0 → P ÷ n, else P·r·(1+r)^n ÷ ((1+r)^n − 1). Round to ₹1 with `Math.round`. Return `null` when any input is missing or ≤ 0.

**Public API**

| Property / method | Type | Purpose |
| --- | --- | --- |
| `@api recordId` | Id | Record-page mode: reads `Amount__c`, `Approved_Amount__c`, `Tenure__c`, `Interest_Rate__c`, `Loan_Product__r.Interest_Rate__c` with `getRecord`; Approved_Amount__c wins when set (same rule as EMI__c). Values can be changed as a what-if; nothing is saved |
| `@api amount` | Number | Input and output in flow mode |
| `@api tenure` | Integer (months) | Input and output in flow mode |
| `@api rate` | Number (annual %) | Passed by the flow from the chosen product; hides the product picker when set |
| `@api minAmount`, `@api maxAmount`, `@api minTenure`, `@api maxTenure` | Number | Bounds from the product; slider limits and validation (BR-03 early feedback) |
| `@api emi` | Number (read-only getter) | Flow output, so the flow can show or store it |
| `@api validate()` | Method | Flow screen validation: returns `{ isValid: false, errorMessage: <label> }` when amount or tenure is outside the bounds |

**Events**

- In a flow: dispatch `FlowAttributeChangeEvent` for `amount`, `tenure` and `emi` on every change (`lightning/flowSupport`).
- Elsewhere: dispatch `CustomEvent('emichange', { detail: { amount, tenure, rate, emi } })`.

**Standalone mode** (utility bar, portal home): no recordId and no rate → show a `lightning-combobox` of active products from Apex.

**Apex `EmiCalculatorController`** (proposed name) — `public with sharing class`

```apex
@AuraEnabled(cacheable=true)
public static List<Loan_Product__c> getActiveProducts()
// SELECT Id, Name, Product_Code__c, Interest_Rate__c, Min_Amount__c, Max_Amount__c,
//        Min_Tenure__c, Max_Tenure__c FROM Loan_Product__c WHERE Active__c = true
// WITH USER_MODE ORDER BY Name
```

**Meta targets:** `lightning__RecordPage` (object Loan_Application__c), `lightning__AppPage`, `lightning__HomePage`, `lightning__UtilityBar`, `lightning__FlowScreen` (properties amount, tenure, rate, minAmount, maxAmount, minTenure, maxTenure as `inputOnly="false"` where the flow needs the value back, emi `role="outputOnly"`), `lightningCommunity__Page`, `lightningCommunity__Default`.

**Labels** (proposed names, add to LAMS-021 set with Hindi): `LAMS_EMI_Title`, `LAMS_EMI_Amount`, `LAMS_EMI_Tenure_Months`, `LAMS_EMI_Product`, `LAMS_EMI_Monthly_EMI`, `LAMS_EMI_Total_Interest`, `LAMS_EMI_Total_Payable`, `LAMS_EMI_Out_Of_Range`. Currency shown with `lightning-formatted-number format-style="currency" currency-code="INR"`.

**Accessibility (NFR-11):** every input has a visible label; the EMI result sits in an `aria-live="polite"` region.

## Steps

1. `sf lightning generate component --type lwc --name emiCalculator --output-dir force-app/main/default/lwc`
2. Write `emiMath.js` first and its Jest test (AC-09 numbers below), then the component.
3. `sf apex generate class --name EmiCalculatorController --output-dir force-app/main/default/classes` and `EmiCalculatorControllerTest`.
4. Run Jest: `npm run test:unit -- --testPathPattern emiCalculator`.
5. Deploy: `sf project deploy start --source-dir force-app/main/default/lwc/emiCalculator --source-dir force-app/main/default/classes`.
6. Add the component to the Loan_Application__c Lightning page and the LAMS app utility bar (Lightning App Builder); retrieve: `sf project retrieve start --metadata FlexiPage CustomApplication:LAMS`.
7. Run Apex tests: `sf apex run test --class-names EmiCalculatorControllerTest --code-coverage --result-format human --wait 10`.
8. Commit: `feat(lwc): emiCalculator with live EMI and Jest tests [LAMS-034]`.

## Learn

- **Pure modules in LWC:** putting the maths in `emiMath.js` makes it testable without rendering and shareable with other components.
- **Flow screen components:** `@api` properties exposed in the meta file become flow inputs/outputs; values only reach the flow through `FlowAttributeChangeEvent`, and `@api validate()` blocks the Next button.
- **`getRecord` + `getFieldValue`** (Lightning Data Service) reads record fields with sharing and FLS, with no Apex.
- **Jest mocks:** `@salesforce/apex/...` and `lightning/uiRecordApi` adapters are emitted with test data (`getRecord.emit(mock)`); `lightning/flowSupport` must be mocked to assert `FlowAttributeChangeEvent`.

## Done when

- [ ] `calculateEmi(100000, 14, 12)` returns 8979 (AC-09 figure); `calculateEmi(120000, 0, 12)` returns 10000; missing input returns `null`
- [ ] Typing a new amount updates the EMI with no Apex call (checked in the browser network tab)
- [ ] Jest covers: formula, rate 0, bounds validation message, `FlowAttributeChangeEvent` fired for amount/tenure/emi, `emichange` fired outside a flow, product pick sets rate and bounds, record mode uses Approved_Amount__c when set
- [ ] `EmiCalculatorControllerTest` asserts only active products return; coverage ≥ 90%
- [ ] Component visible on the application page and in the utility bar; all text comes from custom labels
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-03, BR-04, §10.3 EMI\_\_c, §10.6 EMI formula, §15 emiCalculator, NFR-02, NFR-11, AC-09
