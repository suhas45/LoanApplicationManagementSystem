# LAMS-078 · Queues, Case assignment + escalation rules

**Milestone:** [M10 – Portal](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-56, BR-58

**Depends on:** LAMS-005 (Business Hours "LAMS IST"), LAMS-014 (Case record type Loan Service Request, Request_Type__c, Origin values), LAMS-022 (roles), LAMS-029 (users), LAMS-048 (Credit Managers queue), LAMS-076 (portal *New Service Request* action)

## Goal

Every service request lands with the right team automatically — Disputes with Credit Managers, everything else with Operations (BR-58) — and any request still open after 2 business days is escalated to the Credit Head (BR-56).

## Build

**Business Hours** *LAMS IST* (from LAMS-005): Mon–Sat 09:30–18:00, time zone Asia/Kolkata (8.5 hours a day).

**Queues**

| Queue (API name) | Supported objects | Members |
| --- | --- | --- |
| Credit Managers (`Credit_Managers`, from LAMS-048) | Loan_Application__c, **add Case** | Role: Credit Manager |
| Operations (`Operations`, proposed API name) | Case | Role: Operations Officer |

**Case assignment rule** *LAMS Case Assignment* (active)

| Order | Criteria | Assign to |
| --- | --- | --- |
| 1 | Case: Record Type = Loan Service Request AND Request_Type__c = Dispute | Queue Credit Managers |
| 2 | Case: Record Type = Loan Service Request | Queue Operations |

**Case escalation rule** *LAMS Case Escalation* (active)

| Setting | Value |
| --- | --- |
| Entry criteria | Case: Record Type = Loan Service Request (escalation only applies while the case is open) |
| Business hours | Set business hours: LAMS IST |
| Escalation times | *When case is created* (not the "disable after first modified" or "last modification" options) |
| Action 1 – age | **17 hours** (2 business days × 8.5 h) |
| Auto-reassign to | User: the Credit Head (org-specific username; record in README) |
| Notify | Credit Head (template *LAMS Case Escalated*, proposed, EN) and the current case owner |

**Making the rule fire for every channel**

| Channel | How the assignment rule runs |
| --- | --- |
| Phone (staff create) | Case page layout → Layout Properties → *Assign using active assignment rule* shown and default on |
| Portal (Create Case Form, LAMS-076) | Check a portal case lands in the queue; if it does not, record it in the Parking lot |
| Apex / agent (CreateServiceRequest, LAMS-084) | `Database.DMLOptions dmo = new Database.DMLOptions(); dmo.assignmentRuleHeader.useDefaultRule = true; c.setOptions(dmo);` |

**Test class `CaseRoutingTest`** (proposed): insert Cases with the DML option above → Dispute owned by Credit Managers queue, Statement / Prepayment Quote / Address Change owned by Operations; 200 cases in one insert route correctly.

## Steps

1. Edit the Credit Managers queue to add Case; create the Operations queue.
2. Create the assignment rule and escalation rule (Setup → Case Assignment Rules / Escalation Rules); activate both.
3. Create the *LAMS Case Escalated* email template; update the Case layout's assignment checkbox.
4. Write and run `CaseRoutingTest`.
5. Raise a Dispute from the portal and a Statement request by phone; check owners. Open Setup → Case Escalations to see the pending escalation time.
6. Retrieve: `sf project retrieve start --metadata Queue:Credit_Managers Queue:Operations AssignmentRules:Case EscalationRules:Case EmailTemplate Layout`
7. Commit: `feat(service): Case queues, assignment and escalation rules [LAMS-078]`.

## Learn

- **Assignment rules** evaluate entries in order and stop at the first match; put the narrow rule (Dispute) first.
- Assignment rules do **not** run automatically for Apex or API inserts; you must set `assignmentRuleHeader`.
- **Escalation ages count business hours** only, so "2 business days" is 17 hours with an 8.5-hour day, not 48. The escalation queue is checked about every 15 minutes.
- Queue members by role keep the queue right when people change; reassigning to a named user (Credit Head) is the one org-specific reference here.

## Done when

- [ ] A portal Dispute is owned by the Credit Managers queue; Statement, Prepayment Quote and Address Change by Operations (BR-58)
- [ ] A new open case shows an escalation scheduled 17 business hours after creation in Setup → Case Escalations (BR-56)
- [ ] An escalated case is reassigned to the Credit Head, who gets the email (demo by a short-age test entry, then restore 17 h)
- [ ] `CaseRoutingTest` passes, including the 200-case insert
- [ ] Queues and rules in source; the Credit Head username dependency is noted in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §13.5 Case assignment and escalation, §10.8 Case, §11 Case OWD Private, §8 A5, §17 Borrower Assistant hand-off to the Operations queue, BR-56, BR-57, BR-58
