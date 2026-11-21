# LAMS-089 · Calculated insights, segments, activation write-back

**Milestone:** [M12 – AI and Data Cloud](README.md) · **Size:** L (5–10h) · **Delivers:** BR-78

**Depends on:** LAMS-088 (unified profile and DMOs), LAMS-059 (Days_Past_Due__c set nightly), LAMS-058 (Paid_Date__c from allocation), LAMS-054 (Assigned_Officer__c), LAMS-017 (Data_Cloud_Enabled__c), LAMS-085 (grounding update)

## Goal

Repayment history becomes a repayment score and a pre-approved flag on each borrower's Contact, and an early-risk Task for the assigned officer (BR-78). The milestone exit check is that a clean payer (12 months, no overdue) gets Pre_Approved__c = true.

## Build

Data Cloud screens, SQL functions and activation options vary by release. The definitions below are SQL-like; adjust the function names to your calculated insight editor and verify each setting in your org.

**Calculated insight `LAMS_Repayment_Insights` (proposed container name), keyed by Unified Individual**

Join path: `LAMS_EMI_Instalment__dlm i` → `LAMS_Loan__dlm l` (Loan Id) → the unified link object for Individual (name depends on the ruleset, e.g. `UnifiedLinkssotIndividual…__dlm`, `SourceRecordId__c = l.Borrower_Id__c`) → `UnifiedIndividual__dlm`. Window W12 = instalments with Due_Date between today − 365 days and today, Status ≠ Cancelled. Window W3 = due in the last 90 days.

| Measure | Definition | Source |
| --- | --- | --- |
| `On_Time_Payment_Ratio__c` | `SUM(CASE WHEN paid_date IS NOT NULL AND paid_date <= due_date THEN 1 ELSE 0 END) / COUNT(instalment_id)` over W12 | BRD |
| `Avg_Days_Late__c` | `AVG(GREATEST(0, DATEDIFF(COALESCE(paid_date, CURRENT_DATE), due_date)))` over W12 | BRD |
| `Active_Loan_Count__c` | `COUNT(DISTINCT CASE WHEN l.status = 'Active' THEN l.loan_id END)` | BRD |
| `Avg_Days_Late_3M__c` | Same as Avg_Days_Late over W3 | proposed (for "rising") |
| `Instalments_Due_12M__c` | `COUNT(instalment_id)` over W12 | proposed |
| `Late_Instalments_12M__c` | Count over W12 where paid after due date, or still unpaid and past due | proposed |
| `Max_Days_Past_Due__c` | `MAX(l.days_past_due)` over the borrower's Active loans | proposed |
| `Repayment_Score__c` | `ROUND(GREATEST(0, 100 × On_Time_Payment_Ratio − 2 × Avg_Days_Late))`, 0–100 | proposed formula (BRD names the field, not the formula) |
| `Pre_Approved_Flag__c` | `1` when Instalments_Due_12M ≥ 12 and Late_Instalments_12M = 0 and Max_Days_Past_Due = 0, else `0` | proposed |
| `Early_Risk_Flag__c` | `1` when Max_Days_Past_Due between 1 and 30 and Avg_Days_Late_3M > Avg_Days_Late, else `0` | proposed |

If the editor will not build a measure from other measures, compute the base measures in one insight and the score and flags in a second insight on top of it. Schedule: every 24 hours (proposed); run it manually for the demo.

**Segments** (on Unified Individual)

| Segment | Rule | Publish |
| --- | --- | --- |
| LAMS Clean Payers (proposed name) | Pre_Approved_Flag__c = 1, i.e. 12 months of instalments, none late or overdue | Standard schedule; publish manually for the demo |
| LAMS Early Risk (proposed name) | Early_Risk_Flag__c = 1, i.e. DPD 1–30 and Avg_Days_Late rising | Same |

The segments give a reviewable list (and could be activated to marketing later). The CRM write-back below is driven by the insight fields, so it does not wait for a segment publish.

**Activation 1: Copy Field enrichment on Contact**

| Data Cloud field | → Contact field |
| --- | --- |
| LAMS_Repayment_Insights.Repayment_Score__c | Repayment_Score__c |
| LAMS_Repayment_Insights.Pre_Approved_Flag__c | Pre_Approved__c |

The Contact links to the insight through Individual (Contact Id) → Unified Individual. If your release will not map a number to a checkbox, change Pre_Approved_Flag__c to a Boolean or text dimension the enrichment accepts. Failing that, set Pre_Approved__c from the Activation 2 flow (proposed fallback). Note the choice in the README. Give the Data Cloud integration user edit access to both Contact fields; make them read-only for everyone else. BR-71 does not list Repayment_Score__c, so decide whether Operations may see it and record the decision in the BRD.

**Activation 2: Data Action → Flow → Task (early risk)**

| Piece | Value |
| --- | --- |
| Data action target | Salesforce Platform Event (proposed name `LAMS_Early_Risk_Target`) |
| Data action `LAMS_Early_Risk` (proposed) | Primary object `LAMS_Loan__dlm`. Fires when Days_Past_Due__c changes to a value from 1 to 30. If your release can enrich or filter data actions with insight fields, also require Early_Risk_Flag__c = 1; otherwise the "rising" part is checked in the flow (below) or noted as not enforced |
| Event received in Salesforce | `DataObjectDataChgEvent`; the record values come as JSON in `PayloadCurrentValue` |
| Apex `DataActionPayloadParser` (proposed) | `@InvocableMethod`: takes the JSON payload and returns `loanId` (and DPD). Has its own test with sample payloads, including a missing field and bad JSON |
| Flow `LAMS Early Risk Alert` (proposed), platform event–triggered on DataObjectDataChgEvent | 1. Exit unless `ActionDeveloperName = 'LAMS_Early_Risk'` and `$Setup.LAMS_Settings__c.Data_Cloud_Enabled__c` is true. 2. Parse the payload → Loan__c. 3. Exit if an open Task with the same subject already exists on the loan. 4. Create Task: OwnerId = Loan__c.Assigned_Officer__c, WhatId = loan, WhoId = Borrower__c, Subject = label `LAMS_Early_Risk_Task_Subject` (proposed), Priority High, ActivityDate = today + 1 |

If your release offers a **Data Cloud–triggered flow** (a flow that starts on a DMO or insight change), you may use it instead of the platform event and parser. Keep the same toggle check and task logic.

The flow runs as the Automated Process user (§8 C3). That is why it reads the org-default toggle through `$Setup`.

**Agent grounding (§17 "both agents read the unified profile and insights")**

- Loan Officer Assistant: add a line to `ApplicationSummaryGrounding` (LAMS-085): "Repayment score {Repayment_Score__c}, pre-approved {Pre_Approved__c}". Add it only when Data_Cloud_Enabled__c is on, with a test for on and off.
- Borrower Assistant: not added (proposed). BR-76 does not include telling borrowers their score or pre-approval. Note this in the README.

**Demo data** (anonymous Apex scripts, proposed: `scripts/apex/seed-clean-payer.apex`, `scripts/apex/seed-early-risk.apex`)

| Borrower | Data |
| --- | --- |
| Clean payer | Personal Loan disbursed 13 months ago, 24 months; 12 instalments paid on their due dates through normal Payment__c inserts (allocation sets Paid_Date__c) |
| Early risk | Loan where the last 3 instalments were paid 5–10 days late and the current one is 5 days overdue (run LoanOverdueBatch to set Days_Past_Due__c) |
| Control | Borrower with one recent late payment, now current |

## Steps

1. Run the seed scripts, then `Database.executeBatch(new LoanOverdueBatch(), 200);` to set DPD. Wait for the data streams to refresh (or refresh them manually).
2. Build `LAMS_Repayment_Insights` and run it. Check the three demo borrowers' values in Data Explorer against a hand calculation.
3. Create and publish both segments; check membership (clean payer in Clean Payers, early-risk borrower in Early Risk, control in neither).
4. Create the Copy Field enrichment on Contact and wait for the sync.
5. Build `DataActionPayloadParser` with its test, deploy, then build the flow and the data action and target.
6. Set Data_Cloud_Enabled__c on. Change the early-risk loan's DPD (rerun the batch the next day, or edit Days_Past_Due__c for the demo) and check the Task. Then set the toggle off, repeat and check no Task is created.
7. Add the grounding line to ApplicationSummaryGrounding and its tests.
8. Time each stage (stream refresh, insight run, enrichment sync, data action) and record the latencies in `docs/DATA_CLOUD_SETUP.md` (proposed).
9. Retrieve: `sf project retrieve start --metadata Flow:LAMS_Early_Risk_Alert ApexClass:DataActionPayloadParser ApexClass:DataActionPayloadParserTest ApexClass:ApplicationSummaryGrounding CustomLabels`.
10. Commit: `feat(data-cloud): repayment insights, segments, copy-field and early-risk task [LAMS-089]`.

## Learn

- **Calculated insights** are scheduled SQL aggregations over DMOs, keyed by a profile (here Unified Individual). Dimensions group, measures aggregate. They are batch, not real-time.
- **Segments vs insights:** a segment is a list of profiles that match a rule, refreshed on a publish schedule. A write-back to one record is simpler from insight fields than from segment membership.
- **Activation latency** adds up: CRM stream refresh, identity resolution, insight run, enrichment sync or data action. Expect hours by default. For a demo, trigger each step manually, and never build a process that needs a same-second result.
- **Data Actions** deliver changes out of Data Cloud as platform events or webhooks. The receiving flow must be idempotent and check the toggle, because one change can arrive more than once.

## Done when

- [ ] `LAMS_Repayment_Insights` returns the right ratio, average days late and active loan count for the three demo borrowers (matches a hand calculation)
- [ ] **Exit check:** the clean-payer demo borrower's Contact shows Pre_Approved__c = true and a Repayment_Score__c, written by Data Cloud; the control borrower's is false
- [ ] The early-risk borrower's assigned Operations Officer gets exactly one Task; a repeat event does not create a second Task
- [ ] With Data_Cloud_Enabled__c off, the flow creates no Task and the summary grounding has no score line
- [ ] DataActionPayloadParser and the updated ApplicationSummaryGrounding have ≥ 90% coverage
- [ ] Latency of each stage recorded; manual setup documented for LAMS-092
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.15 BR-78, §17 Data Cloud table (Calculated insights, Segments, Activation, Agent grounding), §10.1 Repayment_Score__c and Pre_Approved__c, §10.5 Days_Past_Due__c and Assigned_Officer__c, §10.6 EMI_Instalment__c, §12 Data_Cloud_Enabled__c, §8 C3, C4, §20 step 12, BR-48, BR-49, BR-71
