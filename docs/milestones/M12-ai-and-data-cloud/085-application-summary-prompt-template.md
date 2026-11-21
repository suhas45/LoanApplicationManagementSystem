# LAMS-085 · Application Summary prompt template

**Milestone:** [M12 – AI and Data Cloud](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-77

**Depends on:** LAMS-002 (Einstein generative AI available), LAMS-043 (Eligibility_Notes__c), LAMS-010 (Application_Document__c), LAMS-084 (SummariseApplication calls this template)

## Goal

A Flex prompt template, *Application Summary*, turns one application, its documents and its product rules into a short summary with risk flags. Officers get a comparable view of every file (BR-77). The template explains and prepares only. It never recommends approving or rejecting (BR-75).

## Build

**Prompt template**

| Setting | Value |
| --- | --- |
| Type | Flex |
| Name / API name | Application Summary / `LAMS_Application_Summary` (API name proposed) |
| Input | `Application`, type Object, `Loan_Application__c` |
| Model | The org's default model (proposed); note the model in the README |
| Grounding | Merge fields from the application and its product, plus one Apex grounding block (below) |

**Apex grounding class `ApplicationSummaryGrounding` (proposed)** gives the documents and the rule checks as plain text. Risk flags are worked out by code, not by the model:

```apex
public with sharing class ApplicationSummaryGrounding {
    @InvocableMethod(CapabilityType='FlexTemplate://LAMS_Application_Summary')
    public static List<Response> build(List<Request> requests) { … }
    public class Request  { @InvocableVariable(required=true) public Loan_Application__c Application; }
    public class Response { @InvocableVariable public String Prompt; }
}
```

The `Request` variable name must match the template input name. Queries use `WITH USER_MODE`, so a user who cannot see a field cannot pull it into a prompt.

| Grounding line | Source |
| --- | --- |
| Documents: one line per row (type, mandatory, status, rejection reason) | Application_Document__c |
| Rule checks: one line per rule, e.g. "Credit score 705 vs minimum 700: OK, 5 points of margin" | Credit_Score__c vs Min_Credit_Score__c; EMI_To_Income__c vs Max_EMI_To_Income__c; LTV__c vs Max_LTV__c (Home and Auto only); Monthly_Income__c vs Min_Monthly_Income__c; age at maturity vs Max_Age_At_Maturity__c; KYC_Status__c |
| Flag markers | `NEAR LIMIT` within the Refer tolerances (`Refer_Score_Tolerance__c`, `Refer_Ratio_Tolerance__c`); `BREACH` beyond them; `MANUAL SCORE` when Credit_Score_Source__c = Manual Override |
| Eligibility | Eligibility_Result__c and Eligibility_Notes__c, or "Eligibility has not run yet" when Eligibility_Run_Date__c is blank |

**Merge fields used directly:** Name, Loan_Product__r.Name, Amount__c, Approved_Amount__c, Tenure__c, Interest_Rate__c, EMI__c, Status__c, Channel__c, Risk_Grade__c, Submitted_Date__c, Property_Value__c / Vehicle_Price__c (when present). **Never include** PAN__c or Payout_Account__c.

**Template text (outline)**

```
You are preparing a credit file summary for a loan officer at a lender.
Use only the facts below. If a fact is missing, say "not available". Do not guess.
Do not recommend approving or rejecting the application, and do not suggest changing the amount.

Application: {!$Input:Application.Name}, {!$Input:Application.Loan_Product__r.Name},
amount ₹{!$Input:Application.Amount__c} for {!$Input:Application.Tenure__c} months … (other merge fields)
{!$Apex:ApplicationSummaryGrounding.Prompt}

Write at most 200 words in these sections:
1. Overview – two sentences.
2. Eligibility and credit – result, grade, score source.
3. Documents – what is verified and what is outstanding.
4. Risk flags – one bullet per NEAR LIMIT, BREACH or MANUAL SCORE line, quoting the rule. Write "None" if there are none.
5. Next step for the officer – a preparation step only (for example, chase a document).
```

**Access:** officers need the *Prompt Template User* permission set (or its equivalent in your release) to run the template. Add it to the three permission set groups that hold LAMS_Agentforce_User, or document the assignment if it cannot go in a group.

**Tests:** `ApplicationSummaryGroundingTest` covers the grounding class. Test an application with no documents, one with a rejected document, a Home Loan with LTV over the limit (BREACH), a score within the tolerance (NEAR LIMIT), a manual override and no eligibility run, plus a bulk run of 200 applications.

## Steps

1. Write and deploy `ApplicationSummaryGrounding` and its test (the template needs the class to exist).
2. In Prompt Builder, create the Flex template with the `Application` input. Insert the merge fields and the Apex resource, and paste the template text.
3. Preview it against three seed applications (Personal Pass, Home with a rejected document, Auto Refer). Check that the risk flags match the grounding lines and that the text never says "approve" or "reject".
4. Check what the Einstein Trust Layer settings in your org do (data masking, audit). The menus vary by release, so describe what you find in the README.
5. Activate the template. Then run SummariseApplication (LAMS-084) once from anonymous Apex or Flow debug and check that the summary comes back.
6. Retrieve: `sf project retrieve start --metadata GenAiPromptTemplate:LAMS_Application_Summary ApexClass:ApplicationSummaryGrounding ApexClass:ApplicationSummaryGroundingTest`.
7. Commit: `feat(agent): Application Summary flex prompt template with Apex grounding [LAMS-085]`.

## Learn

- **Grounding:** the model only knows what the template gives it. Rule checks done by deterministic Apex, with the model only phrasing them, give risk flags that are repeatable and can be audited (O2).
- **Trust layer:** prompts and responses pass through the Einstein Trust Layer (masking, zero data retention with the model provider, toxicity scoring, audit). It is a safety net, not a reason to put PAN in a prompt.
- **Flex vs record templates:** a Flex template takes typed inputs, so an agent action or Apex can call it with any record. Field Generation templates are tied to one field on a page.

## Done when

- [ ] `LAMS_Application_Summary` is active and in source as `GenAiPromptTemplate`
- [ ] The preview for the three seed applications shows all five sections, with risk flags matching the grounding lines
- [ ] No output recommends approval, rejection or an amount change (checked on the three previews)
- [ ] PAN and payout account never appear in the resolved prompt (check the preview's resolved prompt)
- [ ] `ApplicationSummaryGroundingTest` passes with ≥ 90% coverage, including a 200-record bulk case
- [ ] SummariseApplication (LAMS-084) returns a real summary in the org
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §17 prompt template line, §6.15 BR-75, BR-77, §6.2 BR-11 – BR-15, §10.2 product rule fields, §10.3 application fields, §12 Refer tolerances, §21 Agentforce row
