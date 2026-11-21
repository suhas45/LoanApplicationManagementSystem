# LAMS-032 · Application_Document__c, EMI_Instalment__c, Payment__c rules

**Milestone:** [M05 – Validation rules](README.md) · **Size:** S (≤ 2h) · **Delivers:** §13.1

**Depends on:** LAMS-010, LAMS-013, LAMS-021, LAMS-024 (custom permission LAMS_Waive_Late_Fee)

## Goal

Document rejections always carry a reason (BR-18). Late-fee waivers need a reason and the waiver permission (BR-51). Payments are positive and, once saved, can only be reversed, never edited (BR-41, BR-45). That keeps the audit trail and the payment allocation rebuild (LAMS-058) trustworthy.

## Build

| Object | Rule name | Error location | Message = value of label | BR |
| --- | --- | --- | --- | --- |
| Application_Document__c | AD_Rejection_Reason_Required | Rejection_Reason__c | LAMS_VR_Doc_Rejection_Reason_Required | BR-18 |
| EMI_Instalment__c | EMI_Waiver_Reason_Required | Waiver_Reason__c | LAMS_VR_Waiver_Reason_Required | BR-51 |
| EMI_Instalment__c | EMI_Waiver_Needs_Permission | Late_Fee_Waived__c | LAMS_VR_Waiver_Not_Permitted | BR-51 |
| Payment__c | PAY_Amount_Positive | Amount__c | LAMS_VR_Payment_Amount_Positive | BR-41 |
| Payment__c | PAY_Locked_After_Insert | Top of page | LAMS_VR_Payment_Locked | BR-45 |

As in LAMS-031: Description = `Label: <name>; BR-xx`, and Error Message = the label's English value, copied exactly.

```text
AD_Rejection_Reason_Required
AND(
  ISPICKVAL(Status__c, "Rejected"),
  ISBLANK(Rejection_Reason__c)
)

EMI_Waiver_Reason_Required
AND(
  Late_Fee_Waived__c,
  ISBLANK(Waiver_Reason__c)
)

EMI_Waiver_Needs_Permission
AND(
  OR(ISCHANGED(Late_Fee_Waived__c), AND(ISNEW(), Late_Fee_Waived__c)),
  NOT($Permission.LAMS_Waive_Late_Fee)
)

PAY_Amount_Positive
OR(
  ISBLANK(Amount__c),
  Amount__c <= 0
)

PAY_Locked_After_Insert
AND(
  NOT(ISNEW()),
  OR(
    ISCHANGED(Amount__c),
    ISCHANGED(Loan__c),
    ISCHANGED(Reference__c),
    ISCHANGED(Payment_Date__c),
    ISCHANGED(Mode__c)
  )
)
```

Notes:

- Application_Document__c.Rejection_Reason__c is treated as text. If LAMS-010 made it a picklist, use `ISBLANK(TEXT(Rejection_Reason__c))`.
- §13.1 locks Amount, Loan and Reference. §10.7 says "Only Status and Reversal_Reason can change after insert", so Payment_Date__c and Mode__c are locked too. `Loan__c` is the master-detail field from LAMS-013. Also leave *Allow reparenting* off on it.
- The waiver rule checks the **running user's** permission. The Waive Late Fee screen flow (LAMS-060) runs as the user, so it is checked. The nightly LoanOverdueBatch never touches Late_Fee_Waived__c, so it is never blocked.
- No rule here reads a toggle. Late fees being off (`Late_Fees_Enabled__c`) stops fees being *added* (LAMS-059). It doesn't change who may waive one.

**Hindi:** translate each error message in Translation Workbench (*Validation Error Message*) for the three objects, using the LAMS-021 Hindi values.

## Steps

1. Create the 5 rules (Object Manager, or `objects/<Object>/validationRules/<Rule>.validationRule-meta.xml` as shown in LAMS-031).
2. Deploy: `sf project deploy start --source-dir force-app/main/default/objects/Application_Document__c/validationRules force-app/main/default/objects/EMI_Instalment__c/validationRules force-app/main/default/objects/Payment__c/validationRules`.
3. Add the Hindi messages and retrieve: `sf project retrieve start --metadata CustomObjectTranslation:Application_Document__c-hi CustomObjectTranslation:EMI_Instalment__c-hi CustomObjectTranslation:Payment__c-hi` together with the three `CustomObject`s.
4. Try them by hand: reject a document with no reason; edit a saved payment's Amount.
5. Commit: `feat(validation): document, instalment and payment rules [LAMS-032]`.

## Learn

- **`$Permission.<CustomPermission>`** puts the custom permission check inside a validation rule. It stops a user who reaches the field through a list view or the API, not only the flow that hides the button.
- **Immutable records by rule:** FLS can't say "editable on create, read-only afterwards". `NOT(ISNEW()) && ISCHANGED(...)` can, and it still allows the Status/Reversal_Reason change that a reversal needs.
- `ISCHANGED` is always false on insert. Pair it with `ISNEW()` when the insert itself must be checked (the waiver rule).
- Upserts from PaymentCallbackApi (LAMS-070) with an existing Reference__c are updates. Re-sending the same values passes, and a changed amount is blocked, which helps AC-10.

## Done when

- [ ] 5 active rules exist across the three objects with the formulas and messages above, in `force-app/`
- [ ] By hand: rejecting a document without a reason fails; a user without LAMS_Waive_Late_Fee can't tick Late_Fee_Waived__c; editing a saved payment's Amount fails, but setting Status = Reversed with a Reversal_Reason__c succeeds
- [ ] Hindi translations of the 5 messages are in `objectTranslations/`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §13.1 Validation rules, §10.4 Application_Document__c, §10.6 EMI_Instalment__c, §10.7 Payment__c, §11 Custom permissions, BR-18, BR-41, BR-45, BR-51, AC-10
