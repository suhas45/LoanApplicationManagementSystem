# M14 – Sales: leads and campaigns

≈ 16h · 6 work items · Starts after: [M10 – Portal](../M10-portal/README.md) (build it before M11)

**Goal:** Enquiries become assigned leads that officers qualify and convert into draft applications, and campaigns show which offers bring in loans.

**Exit criteria:** AC-17 and AC-18.

**Order inside this milestone:** LAMS-095 → LAMS-096 → LAMS-098 → LAMS-097 → LAMS-099 → LAMS-100.

## Work items

Tick items here; the linked file says what to build.

- [ ] [LAMS-095](095-lead-fields-statuses-sources-conversion-mapping-path.md) · Lead fields, statuses and sources, conversion field mapping, Path with guidance · `M`
- [ ] [LAMS-096](096-lead-queues-assignment-rules-and-duplicate-rules.md) · Lead queues, assignment rules, matching and duplicate rules · `M`
- [ ] [LAMS-097](097-callbackrequest-lwc-controller-and-web-to-lead.md) · callbackRequest LWC + CallbackRequestController (portal guest) and Web-to-Lead form · `L`
- [ ] [LAMS-098](098-leadtrigger-leadconversionservice-tests.md) · LeadTrigger + LeadConversionService (Draft application on convert) + tests · `L`
- [ ] [LAMS-099](099-campaigns-campaign-c-and-pre-approved-membership.md) · Campaign types and member statuses, Loan_Application__c.Campaign__c, pre-approved membership and Applied status flows · `M`
- [ ] [LAMS-100](100-sales-report-types-reports-and-dashboard.md) · Sales report types, reports and Sales dashboard · `M`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: AC-17 and AC-18.
- [ ] Coverage ≥ 90% for every Apex class added in this milestone
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._
