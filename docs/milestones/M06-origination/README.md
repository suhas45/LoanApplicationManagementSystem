# M06 – Origination

≈ 18h · 11 work items · Starts after: [M05 – Validation rules](../M05-validation-rules/README.md)

**Goal:** An application can be captured, submitted, assigned, credit-scored, KYC-checked and given an eligibility result.

**Exit criteria:** AC-04, AC-05, AC-06.

**Order inside this milestone:** LAMS-039 before LAMS-041/LAMS-042; LAMS-043 before LAMS-042 can call it.

## Work items

Tick items here; the linked file says what to build.

- [ ] [LAMS-034](034-emicalculator-lwc-jest-tests.md) · emiCalculator LWC + Jest tests · `M`
- [ ] [LAMS-035](035-new-loan-application-screen-flow.md) · New Loan Application screen flow · `L`
- [ ] [LAMS-036](036-loaneventpublisher-tests.md) · LoanEventPublisher + tests · `S`
- [ ] [LAMS-037](037-ownerassignmentservice-tests.md) · OwnerAssignmentService + tests · `M`
- [ ] [LAMS-038](038-application-submitted-flow.md) · Application Submitted flow · `M`
- [ ] [LAMS-039](039-integrationlogger-integrationretryable.md) · IntegrationLogger + IntegrationRetryable interface + tests · `M`
- [ ] [LAMS-040](040-named-external-credentials-5-pointing-at-mocks.md) · Named + External Credentials (5) pointing at mocks · `S`
- [ ] [LAMS-041](041-creditbureauservice-httpcalloutmock-tests.md) · CreditBureauService + HttpCalloutMock tests · `L`
- [ ] [LAMS-042](042-kycservice-wsdl2apex-webservicemock-tests.md) · KycService (WSDL2Apex) + WebServiceMock tests · `L`
- [ ] [LAMS-043](043-eligibilityservice-pass-refer-fail-tests.md) · EligibilityService (Pass/Refer/Fail) + tests · `L`
- [ ] [LAMS-044](044-override-credit-score-flow.md) · Override Credit Score flow · `S`

## Milestone exit checklist

- [ ] All work items above ticked
- [ ] Exit criteria demoed: AC-04, AC-05, AC-06.
- [ ] Coverage ≥ 90% for every Apex class added in this milestone
- [ ] Devlog entry written in [DEVLOG.md](../DEVLOG.md)
- [ ] BRD updated if the design changed

## Parking lot

_Bugs and ideas found during this milestone. Add them here; don't fix them in the current branch._
