# LAMS-086 · Loan Officer Assistant

**Milestone:** [M12 – AI and Data Cloud](README.md) · **Size:** M (2–5h) · **Delivers:** BR-77

**Depends on:** LAMS-084 (actions), LAMS-085 (prompt template), LAMS-025 (permission set groups with LAMS_Agentforce_User), LAMS-029 (test users)

## Goal

An employee agent in Lightning helps Loan Officers, Credit Managers and the Credit Head prepare files. It can summarise an application, flag risks against product rules and draft a follow-up email (BR-77). It never decides (BR-75), and a person reviews every output before it is saved or sent.

## Build

Agentforce menus change between releases. Build this in Agent Builder (topics) or in the newer Agent Script builder; the spec is the same either way. Verify the labels in your org.

**Agent**

| Setting | Value |
| --- | --- |
| Type | Agentforce Employee Agent |
| Name / API name | Loan Officer Assistant / `LAMS_Loan_Officer_Assistant` (API name proposed) |
| Channel | Lightning Experience: the Agentforce panel in the LAMS app, available on Loan Application record pages |
| Access | Users with `LAMS_Agentforce_User` (in the Loan Officer, Credit Manager and Credit Head groups, §11). Operations does not get it |
| Toggle | Agentforce_Enabled__c, user-scoped (§12). Off → every action returns `LAMS_Agent_Unavailable` and the agent says the assistant is switched off. Use a user-level override to pilot with one Loan Officer |
| Language | English |

**Agent-level instructions (system)**

> You help staff at a lender prepare loan application files. You explain and prepare; you never approve, reject, disburse, change amounts or change any status, and you have no action that can. If asked to, say that decisions are made in the approval process and offer to summarise the file instead. Always show generated text to the user and ask before saving it. Never invent figures; use only action results.

**Topics**

| Topic | Classification description | Instructions (key lines) | Actions |
| --- | --- | --- | --- |
| Application Review | Requests to summarise a loan application, explain its eligibility or credit result, list risks, or check documents | Use the application on the current record page if the user does not name one. Call SummariseApplication without `summaryToSave` and show the full summary. Ask "Save this to the AI Summary field?" Only on a clear yes, call SummariseApplication again with the exact text shown. For document questions, call GetMissingDocuments | SummariseApplication, GetApplicationStatus, GetMissingDocuments |
| Follow-up Email | Requests to write, draft or revise an email to a borrower about their application | Call GetMissingDocuments first. Then call the email draft action. Present the draft as text for the user to copy and send; never send it. Keep the borrower's Preferred_Language__c in mind and say if a Hindi version is needed | GetMissingDocuments, `LAMS_Followup_Email` prompt template action (proposed, below) |
| Decisions Not Allowed (proposed) | Requests to approve, reject, disburse, change an amount, waive a fee or change a status | Decline politely. Explain that the approval process or the relevant quick action handles it, and name the record. Offer to summarise the file instead | none |

**Follow-up email action (proposed).** BR-77 asks for an email draft, but the BRD names only one prompt template. Create a second Flex template, `LAMS_Followup_Email` (proposed), with input `Application` (Loan_Application__c). Ground it on the borrower's name, application number and outstanding documents. Use a template-triggered prompt flow `LAMS_Followup_Email_Grounding` (proposed) that lists Application_Document__c rows in Requested or Rejected. Add the template to the topic as a prompt template action. Output: subject line plus body, under 150 words, no promises about the decision. If your org offers a standard email-drafting action that can take these grounding facts, you may use it instead. Note the choice in the README.

**Action settings in the agent**

| Action | Inputs collected from the user? | Show output in conversation | Require confirmation |
| --- | --- | --- | --- |
| SummariseApplication | `applicationId` from record context or user; `summaryToSave` only from the confirmed summary | Yes | On (proposed) |
| GetApplicationStatus / GetMissingDocuments | Application number from context or user | Yes | Off |
| LAMS_Followup_Email | Application from context | Yes | Off |

`verifiedContactId` is not added for this agent; staff scope comes from sharing.

**Test utterances** (Testing Center or preview)

| Utterance (on an application page) | Expected |
| --- | --- |
| "Summarise this application" | Application Review topic; SummariseApplication called; five sections shown; asks before saving |
| "Yes, save it" | SummariseApplication called with `summaryToSave`; AI_Summary__c updated |
| "What's risky about this file?" | Risk flags section, matching the grounding |
| "Draft an email asking for the missing documents" | Follow-up Email topic; draft lists the right documents; nothing sent |
| "Approve this loan" / "Increase the amount to 8 lakh" | Decisions Not Allowed topic; no action; offers a summary |

## Steps

1. Check in Setup that Agentforce (Einstein generative AI and Agents) is on. LAMS-002 recorded what the org allows.
2. Create `LAMS_Followup_Email` and its grounding flow; preview it.
3. Create the employee agent; paste the system instructions; create the three topics with the descriptions and instructions above. Add the actions and set the input and output options.
4. Give access to the agent through `LAMS_Agentforce_User`. In recent releases you add the agent's access to a permission set. Check it as the Loan Officer and Credit Manager test users.
5. Test the five utterances in the builder's preview, then as a Loan Officer test user in the LAMS app. Then turn off Agentforce_Enabled__c for that user and test again.
6. Optional: save the utterances as a test suite. Use `sf agent generate test-spec`, then `sf agent test create` and `sf agent test run` (check the flags with `--help`; these commands are newer and change often).
7. Retrieve what your release exposes as metadata, for example: `sf project retrieve start --metadata Bot GenAiPlannerBundle GenAiPlugin GenAiFunction GenAiPromptTemplate:LAMS_Followup_Email Flow:LAMS_Followup_Email_Grounding`. Anything that does not retrieve goes in the README's manual steps.
8. Commit: `feat(agent): Loan Officer Assistant employee agent [LAMS-086]`.

## Learn

- **Topics vs actions:** a topic is a job the agent can do, with a classification description (when it applies) and instructions (how to behave). Actions are the tools inside it. The planner first picks a topic, then chooses actions only from that topic.
- **Human in the loop:** "show, confirm, then save" is built from the action design (two calls), the instructions and the confirmation setting together. No one layer is enough alone.
- **A guardrail topic** that catches decision requests makes declining predictable and testable, instead of hoping the model refuses.
- Agent metadata (Bot, GenAiPlannerBundle, GenAiPlugin, GenAiFunction) is still changing. Expect some setup to stay manual and document it.

## Done when

- [ ] As a Loan Officer, "Summarise this application" on a seed application returns the five-section summary, and AI_Summary__c changes only after "yes"
- [ ] A follow-up email draft lists exactly the application's outstanding documents and is not sent
- [ ] "Approve this loan" and "Increase the amount" are declined with no action call (check the action log in preview)
- [ ] An Operations Officer cannot open the agent
- [ ] With Agentforce_Enabled__c off for the pilot user, the agent replies that the assistant is unavailable
- [ ] Agent metadata that can be retrieved is in source; the rest is listed as manual steps for LAMS-092
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.15 BR-75, BR-77, §17 Loan Officer Assistant row and prompt template, §11 LAMS_Agentforce_User and groups, §12 Agentforce_Enabled__c, §10.3 AI_Summary__c, §19 "Not in source", §21 Agentforce row
