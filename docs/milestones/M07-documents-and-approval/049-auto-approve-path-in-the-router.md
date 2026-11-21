# LAMS-049 · Auto-approve path in the router

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-27

**Depends on:** LAMS-046 (ApplicationRouter), LAMS-048 (manual path and decision guard), LAMS-047 (offer email from Application_Decided), LAMS-017 / LAMS-019 (Auto_Approve_Enabled__c, Auto_Approve_Max_Amount__c through FeatureToggle)

## Goal

Small, clean personal loans are approved with no manual step when the feature is on (BR-27); with it off, or when any condition is missed, they go to the Credit Managers as normal (BR-80). Completes **AC-01** and **AC-02**.

## Build

**Fill router step 4** — `private static Boolean isAutoApprove(Loan_Application__c app)` in ApplicationRouter:

| Condition | Source |
| --- | --- |
| Feature on | Auto_Approve_Enabled__c via FeatureToggle (org default) |
| Product allows auto-approve | `Loan_Product__r.Auto_Approve_Eligible__c = true` (only Personal Loan in seed data; BRD v2.1 keeps products as data instead of hardcoding 'PL') |
| Amount | `Amount__c ≤ Auto_Approve_Max_Amount__c` (default 5,00,000; FeatureToggle throws if blank — let it surface) |
| Eligibility | `Eligibility_Result__c = 'Pass'` |
| Grade | `Risk_Grade__c` in A, B |
| KYC | `Borrower__r.KYC_Status__c = 'Verified'` |

Order in the router stays §13.3: KYC Rejected (2) → secured review (3) → **auto-approve (4)** → manual (5).

**Auto-approve action** (same update as other routed records, no approval process):

| Field | Value |
| --- | --- |
| Status__c | Approved |
| Approved_Amount__c | Amount__c |
| Decision_Date__c | today |
| Offer_Expiry_Date__c | today + Offer_Validity_Days__c (FeatureToggle) — stamped, not a formula (§10.3) |
| Decision_Comments__c | label `LAMS_Router_Auto_Approved` ("Auto-approved under BR-27") |

The status change fires `Application_Decided` (LAMS-047): offer email in the borrower's language, Application Approved event, and the OfferLetter PDF once LAMS-051 is in. The decision guard (LAMS-048) passes because score and Pass result are present.

## Steps

1. Implement `isAutoApprove` and the approve branch; keep reads of the toggle and thresholds to one FeatureToggle call per router run.
2. Add tests to `ApplicationRouterTest` (or `ApplicationRouterAutoApproveTest`).
3. `sf project deploy start --source-dir force-app/main/default/classes`
4. `sf apex run test --class-names ApplicationRouterTest --code-coverage --result-format human --wait 10`
5. Demo AC-01 and AC-02 in the org (Credit Head flips the toggle in lamsSettings, LAMS-030).
6. Commit: `feat(apex): auto-approve path in ApplicationRouter [LAMS-049]`.

## Learn

- **Toggle with a manual fallback (BR-80):** "off" is not an error path — the record simply continues to the normal approval, which is what AC-02 proves.
- **Auto-approve leaves no approval history;** the audit trail is field history on Status__c plus Decision_Comments__c, so stamp a clear comment.
- **Boundaries belong in settings,** not code: changing Auto_Approve_Max_Amount__c in lamsSettings changes behaviour in the next transaction (NFR-13).

## Done when

- [ ] **AC-01:** Personal Loan ₹3 lakh, score 790 (grade A), KYC Verified, Pass, auto-approve on → when the last mandatory document is verified the application is Approved with no approval instance, Approved_Amount__c = ₹3 lakh, Offer_Expiry_Date__c = today + 15, and the offer email is sent (re-checked with the OfferLetter PDF in LAMS-051)
- [ ] **AC-02:** same with auto-approve off → Under Review with a pending work item for queue Credit_Managers
- [ ] Each failed condition alone sends it to manual approval: Home Loan, ₹5,00,001, Refer, grade C (score 720), KYC Pending
- [ ] Exactly ₹5,00,000 is auto-approved; with Auto_Approve_Max_Amount__c set to ₹2 lakh the ₹3 lakh case goes to manual
- [ ] Bulk: 200 qualifying applications auto-approved in one router call; a mix of 100 qualifying + 100 not splits correctly
- [ ] Coverage ≥ 90% for ApplicationRouter, toggle on and off
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-14, BR-19, BR-27, BR-28, BR-80, BR-81, §12 Auto\_Approve\_Enabled\_\_c, Auto\_Approve\_Max\_Amount\_\_c, Offer\_Validity\_Days\_\_c, §13.3 step 4, §14 ApplicationRouter, NFR-13, AC-01, AC-02
