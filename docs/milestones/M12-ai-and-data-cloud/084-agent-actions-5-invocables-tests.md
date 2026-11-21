# LAMS-084 · Agent actions (5 invocables) + tests

**Milestone:** [M12 – AI and Data Cloud](README.md) · **Size:** M (2–5h) · **Delivers:** BR-76, BR-77

**Depends on:** M11 done; LAMS-019 (FeatureToggle), LAMS-021 (custom labels), LAMS-024 (LAMS_Agentforce_User), LAMS-055 (EmiScheduleService), LAMS-058 (instalment balances), LAMS-077 (portal sharing set), LAMS-078 (Case assignment rules)

## Goal

Five Apex invocable actions give both agents everything they can do. Each action only reads, or creates a service request, or saves a summary the user has confirmed. None of them approves, rejects, disburses or changes an amount (BR-75). Together they deliver BR-76 (borrower status, documents, EMI, service request) and BR-77 (application summary).

## Build

**Common rules for all five classes**

| Rule | Detail |
| --- | --- |
| Class shape | `public with sharing class <ActionName>`, one `@InvocableMethod` taking `List<Request>` and returning `List<Response>`. Bulk-safe: collect keys, one query per object, no SOQL in loops |
| Data access | Every query uses `WITH USER_MODE`; DML uses `Database.insert(..., AccessLevel.USER_MODE)`. The action runs as the user who is talking to the agent, so sharing and FLS limit what it returns |
| Borrower scope | Helper `AgentBorrowerScope` (proposed), see below. Every borrower-facing query adds `Borrower__c = :scopeContactId` (`ContactId` for Case). An application or loan number from the chat is always combined with that filter, never used alone |
| Toggle | First line: if `Agentforce_Enabled__c` is off for the running user (FeatureToggle, user-scoped `getInstance()`, §12), return `available = false` and the label `LAMS_Agent_Unavailable` (proposed). No query runs |
| Text | Every message returned is a custom label (NFR-09). Labels: `LAMS_Agent_Unavailable`, `LAMS_Agent_Not_Found`, `LAMS_Agent_Request_Created`, `LAMS_Agent_NextStep_<Status>` for each application status (all proposed) |
| Fields never returned to a borrower | PAN__c, Monthly_Income__c, Credit_Score__c, Eligibility_Notes__c, Risk_Grade__c, Decision_Comments__c, Payout_Account__c |
| Errors | Caught and returned as `message` with `success = false`; never thrown to the agent |

**`AgentBorrowerScope` (proposed).** BRD §17 says the Borrower Assistant's actions "run as the portal user". In current releases an Agentforce Service Agent usually runs as its own **agent user**, not as the borrower. Check this in your org (log `UserInfo.getUserName()` from an action in preview). Build for both cases:

| Running user | Scope used |
| --- | --- |
| Portal user (`User.ContactId` not null) | That ContactId; `with sharing` and the sharing set do the rest |
| User with custom permission `LAMS_Borrower_Agent_Context` (proposed; given to the service agent user in LAMS-087) | The input `verifiedContactId`, which LAMS-087 maps from the messaging session's verified contact and hides from the planner. If it is blank, return `LAMS_Agent_Not_Found` and nothing else. The query runs in a small inner `without sharing` class that **always** adds the contact filter |
| Staff user (employee agent) | No contact filter; role hierarchy and sharing decide (BR-70) |

**The five actions**

| Action (class) | Label and description (the planner reads these) | Inputs | Outputs |
| --- | --- | --- | --- |
| `GetApplicationStatus` | *Get Application Status* — "Returns the current status, amount, product and plain-language next step of the borrower's loan applications. Use when the user asks where their application is, whether it is approved, or what happens next. If no application number is given, returns the borrower's most recent applications." | `applicationNumber` (Text, optional, e.g. LA-000123); `verifiedContactId` (Id, hidden) | `available`, `success`, `applicationNumber`, `productName`, `status`, `amount`, `approvedAmount`, `submittedDate`, `offerExpiryDate`, `nextStep`, `summaryText` (up to 5 applications, one line each) |
| `GetMissingDocuments` | *Get Missing Documents* — "Lists the documents still needed for a loan application: items not yet uploaded and items rejected with the reason. Use when the user asks what is missing, why a document was rejected, or why the application is not moving." | `applicationNumber` (Text, required); `verifiedContactId` (Id, hidden) | `available`, `success`, `mandatoryOutstanding` (Number), `docsComplete` (Boolean), `documentsText` (one line per Application_Document__c in Requested or Rejected: type, mandatory, rejection reason) |
| `GetEmiSchedule` | *Get EMI Schedule* — "Returns the EMI amount, next due date, outstanding principal, overdue amount and upcoming instalments for one of the borrower's loans. Also calculates a what-if EMI for a different amount and tenure. Use for questions about EMIs, due dates, balances or 'what would my EMI be if…'." | `loanNumber` (Text, optional, e.g. LN-000045); `rowsToShow` (Number, default 6); `whatIfAmount` (Currency, optional); `whatIfTenureMonths` (Number, optional); `whatIfProductCode` (Text, optional, PL/HL/AL/BL); `verifiedContactId` (Id, hidden) | `available`, `success`, `emiAmount`, `nextDueDate`, `outstandingPrincipal`, `overdueAmount`, `scheduleText` (instalment no, due date, EMI, balance due, status), `whatIfEmi`, `whatIfRate` |
| `CreateServiceRequest` | *Create Service Request* — "Creates a service request for the borrower: Statement, Prepayment Quote, Address Change or Dispute. Use only after the user has confirmed the type and the loan. Returns the case number." | `requestType` (Text, required, one of the 4 Request_Type__c values); `loanNumber` (Text, optional; required except Address Change); `description` (Text, required); `verifiedContactId` (Id, hidden) | `available`, `success`, `caseNumber`, `message` |
| `SummariseApplication` | *Summarise Application* — "Staff only. Generates a summary of a loan application with risk flags against the product rules, using the Application Summary prompt template. Call first without summaryToSave and show the result. Call again with summaryToSave only after the user confirms the text should be saved." | `applicationId` (Id, required); `summaryToSave` (Long Text, optional) | `available`, `success`, `summary`, `saved` (Boolean) |

**Behaviour details**

- **GetApplicationStatus:** `nextStep` comes from `LAMS_Agent_NextStep_<Status>`, e.g. Document Review → "upload or replace the documents on your checklist". Approved also returns the offer expiry date.
- **GetEmiSchedule:** reads EMI_Instalment__c rows where Status__c is not Paid or Cancelled, ordered by Instalment_No__c. The what-if EMI uses the same reducing-balance formula as EmiScheduleService (§10.6), with the rate from the product (`whatIfProductCode`, or the loan's product). Call the existing method; do not copy the formula. It also checks the product's Min/Max amount and tenure (BR-03) and returns a message when the values fall outside them. The what-if result is never saved.
- **CreateServiceRequest:** inserts a Case with record type Loan Service Request, `ContactId` = scope contact, `Loan__c`, `Request_Type__c`, `Origin = 'Agent'`, Subject from a label, Description from input. Set `Database.DMLOptions.assignmentRuleHeader.useDefaultRule = true` so the LAMS-078 rule routes Disputes to Credit Managers and others to Operations (BR-58). A Prepayment Quote then fires the LAMS-061 flow on its own.
- **SummariseApplication:** without `summaryToSave`, it calls the prompt template `LAMS_Application_Summary` (LAMS-085) through `ConnectApi.EinsteinLLM.generateMessagesForPromptTemplate` and returns the text. Nothing is saved. With `summaryToSave`, it updates `AI_Summary__c` in user mode and returns `saved = true` (BR-77: a person reviews before saving). Put the LLM call behind an interface `SummaryGenerator` (proposed) with a `@TestVisible` static instance, so tests use a stub. Generate for at most 10 requests per transaction (proposed); later ones get a "try again" message.

**Tests** (one class per action plus `AgentBorrowerScopeTest`; use TestDataFactory)

| Case | Asserts |
| --- | --- |
| Happy path | Correct fields returned for own application or loan |
| Other borrower's number | Portal user A asks for B's LA number → `LAMS_Agent_Not_Found`, no data (BR-59) |
| Agent-context user | With `LAMS_Borrower_Agent_Context`: blank `verifiedContactId` → not found; with A's Id → only A's records |
| Toggle off / on | `available = false` and no query (assert `Limits.getQueries()` unchanged); on → data |
| Bulk | 200 requests in one call, query count constant |
| Hidden fields | Borrower response text never contains the credit score or PAN |
| CreateServiceRequest | Case created with Origin Agent, assignment rule applied (owner is the right queue); invalid type → `success = false` |
| What-if | 1,00,000 at 14% for 12 months → whatIfEmi 8,979 (AC-09 figures); out-of-range amount → message |
| SummariseApplication | Stub generator returns text, no DML; with `summaryToSave` → AI_Summary__c updated; Operations user (no access) → error message, not exception |

## Steps

1. Create the custom labels and the custom permission `LAMS_Borrower_Agent_Context` (proposed). Add Apex class access for the five classes to `LAMS_Agentforce_User`. Borrower-side class access goes to the agent user's permission set in LAMS-087.
2. Write `AgentBorrowerScope` and its test first, then the five classes. Each label and description is written in full, as above. Every `@InvocableVariable` gets a `label` and a `description` too.
3. Write the test classes alongside each class and run them:
   `sf apex run test --class-names GetApplicationStatusTest --class-names GetMissingDocumentsTest --class-names GetEmiScheduleTest --class-names CreateServiceRequestTest --class-names SummariseApplicationTest --class-names AgentBorrowerScopeTest --code-coverage --result-format human --wait 20`
4. Deploy: `sf project deploy start --source-dir force-app/main/default/classes`.
5. Check each action shows up as an Apex action in Agent Builder (New Agent Action → Apex), but do not add it to an agent yet. That happens in LAMS-086 and LAMS-087.
6. Commit: `feat(agent): five invocable agent actions with tests [LAMS-084]`.

## Learn

- **Descriptions drive planning.** The reasoning engine picks an action by its label and description, and fills inputs from the input descriptions. Vague text gives wrong or missing calls. Say *when* to use the action, not only what it does.
- **Agent safety comes from the actions, not the prompt.** If no action can approve or change an amount, the agent cannot do it however the user asks (BR-75). Instructions are a second layer.
- **The running user matters.** `with sharing` plus `WITH USER_MODE` only protects data when the action runs as the real user. When it runs as an agent user, you must scope by a verified identity that the LLM cannot supply.
- **Invocables are bulk APIs.** Agents usually send one request, but Flow and tests can send 200, so design for the list.

## Done when

- [ ] The five classes and `AgentBorrowerScope` deploy, each with its own test class and ≥ 90% coverage
- [ ] Every invocable method and variable has a label and a planner-oriented description
- [ ] A portal user's test proves another borrower's application and loan are not returned
- [ ] With Agentforce_Enabled__c off for the running user, every action returns `available = false`
- [ ] CreateServiceRequest creates a Case with Origin Agent that the assignment rule routes (Dispute → Credit Managers, others → Operations)
- [ ] SummariseApplication saves AI_Summary__c only when `summaryToSave` is passed
- [ ] No action changes Status__c, Amount__c, Approved_Amount__c or any loan or payment field (code review)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.15 BR-75 – BR-77, §14 Agent actions row, §17 agent table, §12 Agentforce_Enabled__c and FeatureToggle, §10.3 AI_Summary__c, §10.8 Case, §13.5 assignment rule, BR-58, BR-59, AC-09, NFR-09, NFR-10
