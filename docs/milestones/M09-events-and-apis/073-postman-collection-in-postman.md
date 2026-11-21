# LAMS-073 · Postman collection in `postman/`

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** S (≤ 2h) · **Delivers:** §16

**Depends on:** LAMS-068 (token), LAMS-069 (LoanApplicationApi), LAMS-070 (PaymentCallbackApi), LAMS-071 (LoanStatusWebService), LAMS-006 (mock endpoints)

## Goal

One Postman collection exercises every inbound call with assertions, so anyone can prove the APIs work (and that idempotency holds) in a single run. This is the milestone exit check "Postman collection green".

## Build

**Files**

| File | Content |
| --- | --- |
| `postman/LAMS.postman_collection.json` | Collection v2.1, exported |
| `postman/LAMS-dev.postman_environment.json` | Variables with blank secret values |
| `postman/LoanStatusWebService.wsdl` | From LAMS-071 |

**Environment variables**

| Variable | Example | Secret? |
| --- | --- | --- |
| `instanceUrl` | `https://<mydomain>.my.salesforce.com` | No |
| `apiVersion` | the `sourceApiVersion` in `sfdx-project.json` | No |
| `clientId`, `clientSecret` | from LAMS-068 | **Yes**: current value only, initial value blank |
| `accessToken` | set by script | Yes |
| `partnerReference`, `paymentReference`, `loanNumber` | set by scripts / a demo Active loan | No |

**Collection-level pre-request script:** if `accessToken` is empty, call the token endpoint with `pm.sendRequest` (client credentials) and store it. Collection auth = Bearer `{{accessToken}}`.

**Requests and assertions** (each request has a description and `pm.test` checks)

| Folder | Request | Expect |
| --- | --- | --- |
| 00 Auth | POST `/services/oauth2/token` | 200, `access_token` present; saves token |
| 00 Auth | GET `/services/oauth2/userinfo` | 200, Integration User |
| 01 Partner API | POST `/services/apexrest/lams/v1/applications` new (pre-request sets `partnerReference = DSA1-{{$timestamp}}`) | 201, `applicationNumber` starts `LA-` |
| 01 Partner API | same body again | 200, same `applicationId` (BR-06) |
| 01 Partner API | GET `…/applications/{{partnerReference}}` | 200, `status` = Draft, no `pan` key |
| 01 Partner API | GET `…/applications/DOES-NOT-EXIST` | 404 |
| 01 Partner API | POST with amount above product max | 400 |
| 02 Payment Callback | POST `/services/apexrest/lams/v1/payments` (sets `paymentReference = PG-{{$timestamp}}`) | 201, `duplicate` false |
| 02 Payment Callback | same body again | 200, `duplicate` true (AC-10) |
| 02 Payment Callback | same reference, different amount | 409 |
| 02 Payment Callback | unknown `loanNumber` | 404 |
| 03 Loan Status SOAP | POST `/services/Soap/class/LoanStatusWebService` (XML from LAMS-071) | 200, response contains `<found>true</found>` |
| 09 Manual – toggle off | POST partner application with `Partner_API_Enabled__c` off | 503 — excluded from the normal run; run after flipping the toggle in lamsSettings |
| 10 Mocks (optional) | Bureau mock with PAN ending 9; Core Banking mock with loan ending 9 | 503 — documents the failure switches used by LAMS-072 |

## Steps

1. Build the requests in Postman in a workspace collection *LAMS*; add tests to each.
2. Run the collection in the Collection Runner (folders 00–03) until green.
3. Export the collection (v2.1) and environment to `postman/`; open the environment file and confirm `clientSecret` and `accessToken` values are empty.
4. Optional CLI run (also usable later in CI):
   `npx newman run postman/LAMS.postman_collection.json -e postman/LAMS-dev.postman_environment.json --env-var clientId=<id> --env-var clientSecret=<secret> --folder "00 Auth" --folder "01 Partner API" --folder "02 Payment Callback" --folder "03 Loan Status SOAP"`
5. Take a screenshot of the green run for `docs/BRD/images/`.
6. Add a short "How to run the API collection" section to the README.
7. Commit: `chore(postman): LAMS API collection and environment [LAMS-073]`.

## Learn

- **Collection variables and scripts** make runs repeatable: generate a fresh reference, then reuse it to prove idempotency.
- **Initial vs current values:** only initial values are exported and synced; secrets belong in current values.
- SOAP in Postman is a raw XML POST; the OAuth token goes in the envelope's `SessionHeader`, not the `Authorization` header.
- Newman runs the same collection from the command line and can produce JUnit output for CI.

## Done when

- [ ] Collection Runner (folders 00–03) passes every test against the dev org
- [ ] The 503 request passes when `Partner_API_Enabled__c` is off
- [ ] `postman/` holds the collection, environment and WSDL; no secret or token in any file
- [ ] README explains how to run it; screenshot saved
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §16 Integrations (inbound rows, mock behaviour), §14 LoanApplicationApi, PaymentCallbackApi, LoanStatusWebService, §19 Secrets, §20 step 9, BR-06, BR-41, BR-67, AC-10
