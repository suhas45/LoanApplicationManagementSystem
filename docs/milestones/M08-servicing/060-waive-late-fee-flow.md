# LAMS-060 · Waive Late Fee flow

**Milestone:** [M08 – Servicing](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-51

**Depends on:** LAMS-024 (custom permission LAMS_Waive_Late_Fee in LAMS_Credit), LAMS-032 (EMI_Instalment__c waiver validation rule), LAMS-058 (allocation rebuild invocable), LAMS-059 (late fees exist; the batch skips waived rows)

## Goal

A user with waiver authority can remove a late fee from an instalment with a recorded reason. The loan's allocation then re-runs, so money that had paid the fee moves to the next dues (BR-51).

## Build

**Screen flow `Waive_Late_Fee`** (label *Waive Late Fee*), launched by quick action `EMI_Instalment__c.Waive_Late_Fee`.

| Visibility | How |
| --- | --- |
| Button | Dynamic Actions on the EMI Instalment record page. Filter: Advanced → Permission → Custom Permission `LAMS_Waive_Late_Fee`, and `Late_Fee__c` > 0 |
| Flow guard | First Decision: `{!$Permission.LAMS_Waive_Late_Fee}` is false → error screen (label `LAMS_Waive_No_Permission`, proposed) |
| Data guard | `Late_Fee__c` = 0 or `Status__c` is Paid/Cancelled → error screen (label `LAMS_Waive_Not_Allowed`, proposed). A fully paid fee would need a refund, which is out of scope |

Elements:

1. Get Records `EMI_Instalment__c` = `recordId` (Late_Fee__c, Status__c, Loan__c, Instalment_No__c, Loan__r.Name).
2. Decisions as in the table.
3. **Screen *Waive late fee*:** read-only "Loan {Loan__r.Name}, instalment {Instalment_No__c}, late fee ₹{Late_Fee__c}". Waiver reason is a required Long Text input mapped to `Waiver_Reason__c` (Text, max 255).
4. **Update Records** on the instalment: `Late_Fee__c` = 0, `Late_Fee_Waived__c` = true, `Waiver_Reason__c` = input. The LAMS-032 validation rule enforces the reason and the permission again at save.
5. **Apex action** *Rebuild Payment Allocation* (`PaymentAllocationService.rebuildForFlow`) with `{!record.Loan__c}`. Amount_Paid__c may now exceed the row's reduced balance, and the rebuild moves the extra to later rows.
6. Confirmation screen (label `LAMS_Waive_Done`, proposed). A fault path shows the fault message.

All screen text is in custom labels with Hindi translations. The LAMS_Credit permission set grants the custom permission, so Credit Managers and the Credit Head see the button and Operations Officers do not.

## Steps

1. Add the labels. Build the flow and the quick action, and add the action to the EMI Instalment record page with the permission filter.
2. Test as a Credit Manager: waive a ₹180 fee on a partly paid overdue row → fee 0, reason saved, Amount_Paid__c redistributed.
3. Test as an Operations Officer: the button is absent, and opening the flow URL directly shows the no-permission screen.
4. Flow Builder tests do not cover screen flows. Add an Apex case to `PaymentAllocationServiceTest` instead: set a row to waived, call `rebuildForFlow`, and check that the freed amount moves to the next row.
5. Retrieve: `sf project retrieve start --metadata Flow:Waive_Late_Fee QuickAction:EMI_Instalment__c.Waive_Late_Fee FlexiPage CustomLabels`
6. Commit: `feat(flow): Waive Late Fee screen flow [LAMS-060]`.

## Learn

- **Custom permissions** gate UI (Dynamic Actions filters), Flow (`$Permission`), validation rules (`$Permission`) and Apex (`FeatureManagement.checkPermission`). Check in more than one layer, because a hidden button is not security.
- **Screen flows run in user context by default**, so the user's FLS and sharing apply to the Update Records. That is right here, because the validation rule must see the real user.
- A waiver changes Balance_Due__c, which is a formula. Allocation is a full rebuild, so re-running it is always safe.

## Done when

- [ ] A Credit Manager waives a late fee: Late_Fee__c = 0, Late_Fee_Waived__c = true, Waiver_Reason__c saved
- [ ] Saving without a reason fails; an Operations Officer cannot see or run the action
- [ ] After a waiver, the loan's allocation is rebuilt (an overpaid row's extra moves to the next row) and the nightly batch adds no new fee to that row
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.8 BR-51, §10.6 Late_Fee_Waived__c and Waiver_Reason__c, §11 custom permission LAMS_Waive_Late_Fee, §13.1 EMI_Instalment__c rule, §13.2 Waive Late Fee
