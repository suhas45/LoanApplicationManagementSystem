# LAMS-050 · Secured Loan Review orchestration

**Milestone:** [M07 – Documents and approval](README.md) · **Size:** L (5–10h) · **Delivers:** BR-20

**Depends on:** LAMS-046 (router step 3 stub), LAMS-048 (Loan_Approval, Credit_Managers queue, decision guard), LAMS-045 (documentChecklist read-only mode), LAMS-026 (sharing rules), LAMS-029 (test users), LAMS-002 (orchestration run limits noted)

## Goal

Home and Small-Business loans pass three review stages before approval — Loan Officer confirms the file, Credit Manager reviews credit, Operations completes field verification; Cleared goes to Loan Approval, Failed ends in rejection with reason Policy (BR-20). Switching Secured_Review_Enabled__c off sends them straight to approval (BR-80). Completes **AC-03**.

## Build

**Router step 3** (fill `needsSecuredReview` / `startSecuredReview` in ApplicationRouter):

- Condition: `Loan_Product__r.Requires_Field_Verification__c = true` **and** Secured_Review_Enabled__c (FeatureToggle). Which products is data, not code (§10.2).
- Action: Status__c = Under Review, Field_Verification_Status__c = Pending (in the router's one update), **no** approval submission; then for each record `Flow.Interview.createInterview('Secured_Loan_Review', new Map<String, Object>{ 'recordId' => app.Id }).start();` (proposed launch method; one interview per record).
- `@TestVisible static Set<Id> securedReviewStarted` records the Ids. If orchestration interviews cannot start in your org's Apex test context, skip `start()` when `Test.isRunningTest()` and assert the set instead (proposed).

**Orchestration `Secured_Loan_Review`** — label *Secured Loan Review*, type **Autolaunched Orchestration**, input variable `recordId` (Text, available for input).

| Stage | Step | Type / flow (proposed names) | Assigned to | Does |
| --- | --- | --- | --- | --- |
| 1 File Confirmation | 1a Get context | Background: autolaunched flow `SLR_Get_Context` | – | Outputs `ownerId` (application OwnerId) |
| | 1b Confirm file | Interactive: screen flow `SLR_Confirm_File`; starts when 1a completes | Resource `ownerId` (the Loan Officer) | Shows summary and `c:documentChecklist` with `readOnly` = true; required checkbox "File is complete" (label) |
| 2 Credit Review | 2a Review credit | Interactive: screen flow `SLR_Credit_Review` | Queue `Credit_Managers` | Shows Credit_Score__c, Risk_Grade__c, Eligibility_Result__c, Eligibility_Notes__c, EMI_To_Income__c, LTV__c; required checkbox "Credit reviewed"; optional note appended to Decision_Comments__c |
| 3 Field Verification | 3a Verify | Interactive: screen flow `SLR_Field_Verification` | Queue `Operations` (proposed; created here with Loan_Application__c, LAMS-078 adds Case) | Radio Cleared / Failed → Field_Verification_Status__c; comment required when Failed; shows only property value / business details, borrower name and address — never PAN, income or score (BR-71) |
| 4 Outcome | 4a Apply result | Background: autolaunched flow `SLR_Apply_Field_Verification_Result` | – | Cleared → core action **Submit for Approval** (process `Loan_Approval`, object = recordId, submitter = OwnerId). Failed → update Status__c = Rejected, Rejection_Reason__c = Policy, Decision_Comments__c = the verification comment, Decision_Date__c = today |

Each stage exits when all its steps are complete; stages run in order.

**Operations access (needed because Operations normally sees only Approved / Offer Accepted applications, §11)**

- **Criteria sharing rule** `Secured_Review_Operations` (proposed) on Loan_Application__c: Status__c = Under Review **and** Record Type in (Home, Business) → role Operations Officer, **Read Only**. It lets the Operations Officer open the record and its work guide; it closes again when the status moves on.
- `SLR_Field_Verification` runs **System Context Without Sharing – Access All Data**, so it can write Field_Verification_Status__c although the user has read-only record access; it touches only that field and Decision_Comments__c.
- FLS still hides PAN, income and score from Operations on the record page (LAMS-027).

**Record page:** add the **Orchestration Work Guide** component to the Home and Business application Lightning pages; assignees also see their items in *My Work Items* on the Home page.

## Steps

1. Build the five step flows (`SLR_Get_Context`, `SLR_Confirm_File`, `SLR_Credit_Review`, `SLR_Field_Verification`, `SLR_Apply_Field_Verification_Result`) with labels for all screen text.
2. Create queue `Operations` (role Operations Officer as member) and the sharing rule.
3. Build the orchestration in Flow Builder (New → Autolaunched Orchestration); activate.
4. Fill router step 3; add tests to `ApplicationRouterTest`.
5. Add the Orchestration Work Guide to the Home and Business record pages.
6. Retrieve: `sf project retrieve start --metadata Flow:Secured_Loan_Review Flow:SLR_Get_Context Flow:SLR_Confirm_File Flow:SLR_Credit_Review Flow:SLR_Field_Verification Flow:SLR_Apply_Field_Verification_Result Queue:Operations SharingRules:Loan_Application__c FlexiPage`
7. `sf apex run test --class-names ApplicationRouterTest --code-coverage --result-format human --wait 10`
8. Run AC-03 by hand, logging in as each test user in turn; screenshot the work guide.
9. Commit: `feat(orchestration): Secured Loan Review with field verification [LAMS-050]`.

## Learn

- **Orchestration = stages of steps:** stages run in sequence; steps inside a stage can run in parallel or wait on start conditions. Interactive steps create work items for a user, queue or group; background steps run autolaunched flows with no user.
- **Orchestration vs approval process:** orchestration coordinates *work by different teams*; the approval process records *the decision* and its history. Here one hands over to the other.
- **Access for workers:** assigning a work item does not share the record; plan record access (sharing rule) and field access (FLS, flow run mode) for each assignee.
- Developer Edition limits orchestration runs (C1); check the count in LAMS-002 before load-testing.

## Done when

- [ ] Home Loan with documents and eligibility done → Status Under Review, Field_Verification_Status__c Pending, orchestration running, no approval instance yet
- [ ] Stage 1 work item goes to the owning Loan Officer, stage 2 to Credit_Managers, stage 3 to Operations; each appears in the record's work guide
- [ ] Operations can open the application during Under Review, cannot see PAN, income or score, and can set Cleared/Failed only through the step
- [ ] Failed → Rejected with reason Policy, the comment and Decision_Date__c; rejection email sent
- [ ] **AC-03:** Home Loan ₹60 lakh → stages complete with Cleared → submitted to Loan Approval → Credit Manager approves → still pending with Credit_Head → Credit Head approves → Approved
- [ ] Secured_Review_Enabled__c off → the same Home Loan goes straight to Loan Approval (BR-80); Personal and Auto loans never start the orchestration
- [ ] Router tests: secured branch, toggle off, bulk 200 (secured Ids recorded, no approval submitted); coverage ≥ 90%
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): BR-20, BR-22, BR-71, BR-80, §5 Under Review, §10.2 Requires\_Field\_Verification\_\_c, §10.3 Field\_Verification\_Status\_\_c, §11 sharing, §12 Secured\_Review\_Enabled\_\_c, §13.2 Secured Loan Review, §13.3 step 3, §13.4, C1, AC-03
