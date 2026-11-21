# LAMS-057 · emiSchedule + loanSummaryCard LWCs

**Milestone:** [M08 – Servicing](README.md) · **Size:** M (2–5h) · **Delivers:** BR-40, BR-49

**Depends on:** LAMS-055 (instalment rows exist), LAMS-056 (an Active loan to look at), LAMS-015 (Loan Lightning record page), LAMS-034 (Jest set up for LWC)

## Goal

Staff and borrowers see each instalment's due date, split, paid amount and balance (BR-40). The loan header shows outstanding principal, next due date, days past due and bucket at a glance (BR-49). Both components are reused on the portal's My Loans page in M10.

## Build

**LWC `emiSchedule`** — targets `lightning__RecordPage` (object Loan__c), `lightningCommunity__Page` and `lightningCommunity__Default`. `@api recordId` is set to `{!recordId}` in Experience Builder.

| Column (label from custom label) | Field |
| --- | --- |
| No. | Instalment_No__c |
| Due date | Due_Date__c |
| EMI | EMI_Amount__c |
| Principal | Principal_Component__c |
| Interest | Interest_Component__c |
| Late fee | Late_Fee__c (shows "Waived" when Late_Fee_Waived__c) |
| Closing balance | Closing_Balance__c |
| Paid | Amount_Paid__c |
| Balance due | Balance_Due__c |
| Status | Status__c, as a badge |

- `lightning-datatable`, key field Id, currency columns `type: 'currency'` with `currencyCode: 'INR'`, sorted by Instalment_No__c. Rows with Status Overdue get a row class with a warning colour **and** the status text (NFR-11: never colour alone).
- A footer line shows totals for EMI, Paid and Balance due, plus a Refresh button (`refreshApex`).
- Empty state: label `LAMS_No_Schedule_Yet` ("Schedule appears after disbursement").

**Apex controller `EmiScheduleController`** (proposed name) — `public with sharing class`.
`@AuraEnabled(cacheable=true) public static List<EMI_Instalment__c> getInstalments(Id loanId)` runs `SELECT … FROM EMI_Instalment__c WHERE Loan__c = :loanId WITH USER_MODE ORDER BY Instalment_No__c`. USER_MODE enforces FLS and sharing, so a portal user only sees their own loan's rows through the sharing set (BR-59).

**LWC `loanSummaryCard`** — target `lightning__RecordPage` (Loan__c, header region) and the community targets. It uses Lightning Data Service `getRecord` (no Apex) with these fields:

| Tile | Field |
| --- | --- |
| Outstanding principal | Outstanding_Principal__c |
| Next due date | Next_Due_Date__c |
| EMI | EMI_Amount__c |
| Overdue amount | Overdue_Amount__c |
| Days past due | Days_Past_Due__c |
| Bucket | Overdue_Bucket__c: badge Current = success, Soft = warning, Watch = warning, Substandard = error, Critical = error (SLDS `slds-theme_*`); text always shown |
| Status | Status__c, Disbursement_Status__c |

All labels are custom labels with Hindi translations (BR-54, NFR-12). The components show amounts only; they offer no actions.

## Steps

1. `sf lightning generate component --type lwc --name emiSchedule --output-dir force-app/main/default/lwc` (and the same for `loanSummaryCard`).
2. Write `EmiScheduleController` and `EmiScheduleControllerTest`: rows come back in order, and `System.runAs` an Operations Officer who is not assigned gets 0 rows (sharing) or an exception (USER_MODE).
3. Build both components with the labels via `@salesforce/label/c.*` imports.
4. Jest tests in `__tests__/`:
   - `emiSchedule`: mock the Apex wire with `createApexTestWireAdapter`, emit 12 rows → 12 datatable rows, totals correct; emit [] → empty-state text; emit error → error panel
   - `loanSummaryCard`: emit a `getRecord` mock with bucket Watch → warning badge and text "Watch"; DPD 0 → Current
   - `npm run test:unit -- emiSchedule loanSummaryCard`
5. Add both components to the Loan record page (summary card in the header, schedule in a "Schedule" tab). Deploy: `sf project deploy start --source-dir force-app/main/default/lwc --source-dir force-app/main/default/flexipages`
6. Commit: `feat(lwc): emiSchedule and loanSummaryCard [LAMS-057]`.

## Learn

- **LDS vs Apex:** `getRecord` caches and refreshes itself when the record changes, and it respects FLS. A child list (instalments) needs Apex or `getRelatedListRecords`, and Apex wires must be refreshed with `refreshApex`.
- **Roll-ups recalculate on the server:** Next_Due_Date__c, Overdue_Amount__c and Principal_Repaid__c change when instalments change. After a payment, the card shows new values on the next LDS refresh.
- `WITH USER_MODE` in SOQL enforces both CRUD/FLS and record sharing. `with sharing` alone does not check FLS.
- Experience Cloud (Aura sites) can host LWCs only when the meta file lists the `lightningCommunity__*` targets.

## Done when

- [ ] On an Active loan, emiSchedule shows all rows with the 10 columns; the AC-09 loan shows 12 rows ending in closing balance ₹0
- [ ] loanSummaryCard shows outstanding principal, next due date, DPD and bucket; changing Days_Past_Due__c to 45 shows "Watch"
- [ ] Overdue rows are marked with text and colour; the components pass an accessibility check in Jest (`@sa11y/jest`, `await expect(element).toBeAccessible()`)
- [ ] Jest tests pass; `EmiScheduleControllerTest` passes with ≥ 90% coverage
- [ ] Labels show in Hindi for a user whose language is Hindi
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.7 BR-40, §6.8 BR-49, §6.11 BR-59, BR-60, §10.5 Loan__c roll-ups and formulas, §10.6 EMI_Instalment__c, §15 emiSchedule and loanSummaryCard, NFR-11, NFR-12
