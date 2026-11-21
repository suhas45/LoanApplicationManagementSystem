# M09 – Events and APIs

≈ 14h · 8 work items · Starts after: [M08 – Servicing](../M08-servicing/README.md)

**Goal:** External systems can submit applications, post payments, look up loans and subscribe to events; failed calls retry.

**Exit criteria:** Postman collection green; a failed call retries to Gave Up.

## Work items

Tick items here; the linked file says what to build.

- [ ] [LAMS-066](066-loan-event-handler-platform-event-flow.md) · Loan Event Handler (platform event flow) · `S`
- [ ] [LAMS-067](067-corebankingsyncqueueable-loaneventtrigger.md) · CoreBankingSyncQueueable + LoanEventTrigger + PaymentChangeEventTrigger + tests · `L`
- [ ] [LAMS-068](068-integration-user-external-client-app-client.md) · Integration User + External Client App (client credentials) · `M`
- [ ] [LAMS-069](069-loanapplicationapi-tests.md) · LoanApplicationApi + tests · `M`
- [ ] [LAMS-070](070-paymentcallbackapi-tests.md) · PaymentCallbackApi + tests · `M`
- [ ] [LAMS-071](071-loanstatuswebservice-tests.md) · LoanStatusWebService + tests · `S`
- [ ] [LAMS-072](072-integrationretrybatch-schedule-tests.md) · IntegrationRetryBatch + schedule + tests · `M`
- [ ] [LAMS-073](073-postman-collection-in-postman.md) · Postman collection in `postman/` · `S`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: Postman collection green; a failed call retries to Gave Up.
- [ ] Coverage ≥ 90% for every Apex class added in this milestone
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._
