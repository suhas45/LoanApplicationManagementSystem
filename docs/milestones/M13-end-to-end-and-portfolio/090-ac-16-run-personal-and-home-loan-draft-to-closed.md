# LAMS-090 · AC-16 run: Personal and Home loan, Draft to Closed

**Milestone:** [M13 – End to end and portfolio](README.md) · **Size:** M (2–5h) · **Delivers:** AC-16

**Depends on:** M01 – M12 done; LAMS-006 and LAMS-040 (mocks and credentials), LAMS-020 (settings script), LAMS-029 (test users), LAMS-073 (Postman collection)

## Goal

Run one Personal Loan and one Home Loan through the whole lifecycle, Draft to Closed, as the real users would. Every integration runs against its mock, and you record the evidence. This proves AC-16, and with it that the parts built in M02 – M12 work together.

## Build

The deliverable is a scripted run plus an evidence file, `docs/AC-16-run.md` (proposed). Screenshots go in `docs/BRD/images/ac16-*.png`. No new metadata is built. Bugs found go to the parking lot; fix each under a new item number after 093 before you sign off.

**Settings for the run** (start from the LAMS-020 script, then set these in the lamsSettings LWC as the Credit Head)

| Setting | Value | Why |
| --- | --- | --- |
| Bureau_Mock_Mode__c, KYC_Mock_Mode__c, Payout_Mock_Mode__c | true | AC-16 "every integration in mock mode" |
| SMS_Enabled__c, Core_Banking_Sync_Enabled__c, Partner_API_Enabled__c, Event_Publishing_Enabled__c | true | Exercise SMS, core banking, partner API and events; their Named Credentials point at the public mocks (LAMS-040) |
| Auto_Approve_Enabled__c | true | Personal Loan takes the auto-approve path |
| Secured_Review_Enabled__c | true | Home Loan takes Secured Loan Review |
| Late_Fees_Enabled__c, Portal_Enabled__c | true | |
| Agentforce_Enabled__c, Data_Cloud_Enabled__c | true if M12 passed | Optional checks P11, H15 |

**Actors:** Borrower 1 and Borrower 2 (portal users), Loan Officer 1, Credit Manager, Credit Head, Operations Officer 1, Partner (Postman as Integration User). Borrower 1's PAN must make the bureau mock return a score of 780 or more; neither PAN may end in 9 (that triggers the mock's 503, §16).

**Script A: Personal Loan, ₹3,00,000, 12 months, via the portal**

| # | Actor | Action | Expected | BR / AC |
| --- | --- | --- | --- | --- |
| P1 | Borrower 1 | Home: try the EMI calculator. Apply: Personal, ₹3,00,000, 12 months; **Save Draft** | Draft, Channel Portal; live EMI shown | BR-01, BR-04 |
| P2 | Borrower 1 | My Applications: open the draft; **Submit** | Document Review; Interest_Rate__c 14% copied; owner reassigned to a Loan Officer; checklist rows created; Submitted email in the borrower's language; SMS log row | BR-07, BR-09, BR-16, BR-52 – BR-54, AC-06 |
| P3 | System | Wait up to 2 minutes | Credit_Score__c set, source Bureau; KYC Verified; Eligibility Pass; Eligibility_Run_Date__c set; Credit Bureau and KYC log rows Success | BR-10 – BR-14, NFR-03 |
| P4 | Borrower 1 | Upload every mandatory document (PDF/JPG/PNG) | Items Uploaded | BR-17 |
| P5 | Loan Officer 1 | Verify every document | Router auto-approves: Approved, Decision_Date today, Offer_Expiry_Date today + 15, OfferLetter PDF, offer email | BR-19, BR-27, BR-28, AC-01 |
| P6 | Borrower 1 | Respond to Offer → **Accept** | Offer Accepted; Loan__c Pending Disbursement with Application_Key__c; Operations Officer assigned; Loan__Share for that officer; LoanAgreement PDF | BR-29, BR-33, BR-70 |
| P7 | Operations Officer 1 | Disburse Loan; confirm the payout account | In Progress, then Disbursed: Active, UTR recorded, 12 EMI rows, payout = principal − 2% fee (₹2,94,000); Disbursed email; core banking Synced | BR-34 – BR-39 |
| P8 | Partner (Postman) | PaymentCallbackApi: pay instalment 1's EMI; send the same reference again | One Payment__c; instalment 1 Paid (advance payment); second call rejected as duplicate | BR-41 – BR-43, AC-10 |
| P9 | Borrower 1 | Service Requests: raise **Prepayment Quote** for the loan | Case routed to Operations; Prepayment_Quote_Amount__c set; Prepayment Quote email | BR-44, BR-57, BR-58 |
| P10 | Partner (Postman) | PaymentCallbackApi: pay the quoted amount | Loan Closed, Closure_Type Prepaid; remaining instalments Cancelled; ClosureLetter; Loan Closed email; core banking Synced | BR-44, BR-46, BR-47 |
| P11 | Borrower 1 (optional) | Borrower Assistant: "What's my loan status?" | Correct answer from GetEmiSchedule / GetApplicationStatus | BR-76 |

**Script B: Home Loan, ₹60,00,000, 240 months, via the partner API**

| # | Actor | Action | Expected | BR / AC |
| --- | --- | --- | --- | --- |
| H1 | Partner (Postman) | POST `/lams/v1/applications` for Borrower 2: Home, ₹60,00,000, 240 months, Property_Value__c ₹90,00,000, External_Reference__c `E2E-HL-001`; send it twice | One application, Draft, Channel Partner API, Partner API log rows | BR-01, BR-05, BR-06 |
| H2 | Partner (Postman) | Submit as defined in LAMS-069; then GET status by reference | Document Review, owner a Loan Officer; GET returns the status | BR-06, BR-07 |
| H3 | System | Wait for score and KYC | Eligibility Pass, LTV 66.67% (under 80%) | BR-11 |
| H4 | Borrower 2 | Upload all mandatory documents, including Property Papers | Uploaded | BR-17 |
| H5 | Loan Officer 1 | Verify every document | Secured Loan Review starts (Requires_Field_Verification__c) | BR-20 |
| H6 | Loan Officer 1 → Credit Manager → Operations Officer 1 | Stage 1 confirm file; stage 2 credit review; stage 3 Field_Verification_Status__c Cleared | Submitted to Loan Approval; Under Review | BR-20 |
| H7 | Credit Manager | Reduce Approved_Amount__c to ₹55,00,000; approve | EMI recalculated; still above ₹25 lakh, so it waits for the Credit Head | BR-22, BR-25, AC-03 |
| H8 | Credit Head | Approve | Approved; offer letter; email; approval history shows two steps | BR-22, BR-28 |
| H9 | Loan Officer 1 | Respond to Offer (quick action) on the borrower's behalf → Accept | Offer Accepted; loan created with principal ₹55,00,000 | BR-29 |
| H10 | Operations Officer 1 | Disburse Loan. Optional: first use the mock's failure value to show a failed payout and task, then retry | Active; 240 EMI rows; payout = principal − 0.5% fee (₹54,72,500) | BR-35 – BR-37, AC-08 |
| H11 | Partner (Postman) | PaymentCallbackApi: pay instalment 1's EMI | Instalment 1 Paid | BR-41 |
| H12 | Legacy (Postman SOAP) | LoanStatusWebService for the LN number | Active, outstanding principal matches the loan | BR-67 |
| H13 | Operations Officer 1 | Raise a Prepayment Quote Case for the borrower; record a Bank Transfer Payment__c for the quoted amount | Loan Closed, Prepaid; future rows Cancelled; ClosureLetter; Loan Closed email | BR-44, BR-46 |
| H14 | Legacy (Postman SOAP) | LoanStatusWebService again | Closed, outstanding 0 | BR-67 |
| H15 | Loan Officer 1 (optional) | Loan Officer Assistant: summarise the closed application | Summary returned; saved only on confirm | BR-77 |

Both loans close by prepayment because a 12- or 240-month schedule cannot run to maturity in one session. The Matured path (all instalments paid) is covered by the LAMS-058 tests; say so in the evidence file.

**Closing checks**

| Check | How | Expected |
| --- | --- | --- |
| Every integration called and logged | `SELECT Integration__c, Status__c, COUNT(Id) n FROM Integration_Log__c WHERE CreatedDate = TODAY GROUP BY Integration__c, Status__c` | A Success row for each of Credit Bureau, KYC, Payout, SMS, Core Banking, Partner API, Payment Callback, Loan Status SOAP; PAN and account numbers masked in Request__c/Response__c (BR-65) |
| Audit trail | Field history on both applications and loans; approval history on the Home Loan | Every status change listed (BR-73) |
| Dashboards | Origination, Portfolio, Integrations | The two applications, loans and calls appear (BR-62 – BR-64) |
| Access | Operations Officer opens the Personal Loan application | PAN, income and score not visible (AC-14) |

## Steps

1. Reset demo data if needed (seed plan from LAMS-016), run the settings script, and set the run values above. Write the setting values into `docs/AC-16-run.md`.
2. Run Script A step by step in separate browser profiles (one per user), so sessions do not mix. Note the record numbers, timestamps and a pass or fail for each row.
3. Run Script B the same way, using the Postman collection from LAMS-073 for H1, H2, H11, H12, H14.
4. Run the closing checks: `sf data query --query "SELECT Integration__c, Status__c, COUNT(Id) n FROM Integration_Log__c WHERE CreatedDate = TODAY GROUP BY Integration__c, Status__c" --result-format human`.
5. Take the screenshots: Closed loans, approval history, integration log counts, both letters, the dashboards.
6. Any failure: log it in the M13 parking lot, fix it under a new item, and rerun the affected script from the start.
7. Commit: `test(e2e): AC-16 Personal and Home loan Draft to Closed evidence [LAMS-090]`.

## Learn

- **An end-to-end run tests the joins:** async chains (bureau → KYC → eligibility → router), record locks during approval, sharing after reassignment, and emails across user contexts. Unit tests rarely catch these.
- **Mock design pays off here:** request values that choose success or failure (§16) let you show retries and failures on demand, without editing code.
- **Evidence beats memory:** record numbers, timestamps and screenshots make the run repeatable for the demo video and believable to a reviewer.

## Done when

- [ ] **AC-16:** the Personal Loan and the Home Loan both run from Draft to Closed with every integration in mock mode; every row in Scripts A and B is marked pass in `docs/AC-16-run.md`
- [ ] The Integration_Log__c query shows a Success row for all eight integrations, with masked PAN and account numbers
- [ ] The Home Loan's approval history shows Credit Manager and Credit Head steps; the Personal Loan shows auto-approval
- [ ] Duplicate payment reference and repeated partner reference each created nothing new
- [ ] Screenshots saved in `docs/BRD/images/` and linked from the evidence file and the devlog
- [ ] Every bug found is fixed under its own item, or parked with a reason
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §9 AC-16 (and AC-01, AC-03, AC-06, AC-08, AC-10, AC-14 met along the way), §5 lifecycle and product values, §12 toggles, §13.2 – §13.4 flows, router and approval, §14 origination chain, §16 integrations and mock behaviour, BR-01 – BR-73, §20 step 13
