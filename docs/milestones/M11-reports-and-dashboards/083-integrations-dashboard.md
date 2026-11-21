# LAMS-083 · Integrations dashboard

**Milestone:** [M11 – Reports and dashboards](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-64

**Depends on:** LAMS-080 (Integration Logs report type, folder), LAMS-072 (retries and Gave Up rows exist), LAMS-024 (`LAMS_Policy_Admin` View All on Integration_Log__c)

## Goal

The Credit Head sees calls, failures, retries and Gave Up by integration on one dashboard, so integration health is visible without querying logs (BR-64, BR-65, O6).

## Build

**Reports** in *LAMS Integration Reports* (names proposed), all on report type **Integration Logs**, filter Created Date = LAST 30 DAYS (proposed)

| Report | Format, groupings | Extra filters | Summaries |
| --- | --- | --- | --- |
| Calls by Integration and Status | Matrix: rows Integration__c, columns Status__c | – | Record Count |
| Failures by Integration | Summary by Integration__c | Status__c in Failed, Retrying, Gave Up | Record Count |
| Retries by Integration | Summary by Integration__c | Retry_Count__c > 0 | Sum Retry_Count__c |
| Gave Up | Tabular: Name, Integration, Related Record Id, HTTP Status, Retry Count, Created Date | Status__c = Gave Up | Record Count |
| Average Duration (optional) | Summary by Integration__c | Status__c = Success | Average Duration_Ms__c |

**Dashboard** *LAMS Integrations* (folder *LAMS Integration Dashboards*, proposed, shared with role Credit Head only)

| Setting | Value |
| --- | --- |
| View dashboard as | **Another person: the Credit Head** (static, `dashboardType = SpecifiedUser`; username recorded in README). In the `Lams` org that is the admin, who acts as Credit Head (LAMS-029) |
| Scheduled refresh | Daily 08:00 (proposed); allowed because it is not dynamic |

| Component | Source | Chart |
| --- | --- | --- |
| Calls (30 days) | Calls by Integration and Status | Metric |
| Calls by integration and status | Calls by Integration and Status | Stacked bar, Success / Failed / Retrying / Gave Up |
| Failures | Failures by Integration | Horizontal bar |
| Retries | Retries by Integration | Horizontal bar |
| Gave Up | Gave Up | Metric (red when > 0) + Lightning table |
| Avg duration (optional) | Average Duration | Vertical bar |

## Steps

1. Generate some failures: submit an application with a PAN ending in 9 and run `IntegrationRetryBatch` until it gives up (LAMS-072); post a few payments and partner applications from Postman (LAMS-073).
2. Build the reports and the dashboard; set the running user to the Credit Head.
3. Restrict the dashboard folder to the Credit Head role: anyone who can open it sees the data as the Credit Head.
4. Schedule the refresh.
5. Retrieve: `sf project retrieve start --metadata "Report:LAMS_Integration_Reports/*" "Dashboard:LAMS_Integration_Dashboards/*"` (actual folder API names).
6. Commit: `feat(reports): Integrations dashboard [LAMS-083]`.

## Learn

- **Static running user:** every viewer sees what the running user sees. That is fine for the Credit Head's own view, and the reason the folder must stay restricted.
- Static dashboards do not use the dynamic dashboard allowance and can be scheduled; dynamic ones cannot.
- Integration_Log__c is Private (§11); the Credit Head reads all rows through View All in `LAMS_Policy_Admin`.
- A log row for every call (BR-65) is what makes this dashboard possible; a call that is not logged is invisible here.

## Done when

- [ ] The dashboard shows calls by integration and status for at least Credit Bureau, Partner API and Payment Callback
- [ ] The Gave Up component shows the forced bureau failure from LAMS-072
- [ ] The running user is the Credit Head and only the Credit Head role can open the folder
- [ ] Reports and dashboard in source; running-user username noted in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §18 Dashboards (Integrations) and Integration Logs report type, §10.9 Integration_Log__c, §11 OWD and `LAMS_Policy_Admin`, §16 mock behaviour, BR-64, BR-65, BR-66, O6
