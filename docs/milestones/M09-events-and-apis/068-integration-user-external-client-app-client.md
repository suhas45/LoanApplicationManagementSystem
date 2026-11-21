# LAMS-068 · Integration User + External Client App (client credentials)

**Milestone:** [M09 – Events and APIs](README.md) · **Size:** M (2–5h) · **Delivers:** §16

**Depends on:** LAMS-023 (Integration User profile), LAMS-024 (`LAMS_Integration` permission set), LAMS-029 (Integration User created), LAMS-003 (My Domain URL and API version known)

## Goal

Partners, the payment gateway and the legacy system call LAMS as one API-only identity, the **Integration User**, using an OAuth client credentials token from an External Client App, so no human password is shared and every inbound call is attributable (§4, §11, §16).

## Build

**Integration User** (created in LAMS-029; check these settings)

| Setting | Value |
| --- | --- |
| User licence | Salesforce Integration |
| Profile | The Integration User profile from LAMS-023 (based on *Minimum Access – API Only Integrations*) |
| Permission set licence | Salesforce API Integration (must be assigned before custom permission sets) |
| Permission set | `LAMS_Integration` |
| Role | None |

**Add to `LAMS_Integration`** (needed by LAMS-069 – LAMS-071; items marked proposed are not in BRD §11):

| Permission | Why |
| --- | --- |
| Apex Class Access: `LoanApplicationApi`, `PaymentCallbackApi`, `LoanStatusWebService` | Without it the endpoints return 403 / `INSUFFICIENT_ACCESS`. Add each class as it is built |
| Read on `Loan_Product__c` (proposed) | Partner API resolves `productCode` |
| Create/Read/Edit on `Account`, `Contact` (proposed) | Partner API upserts the borrower by PAN |
| Read on `Loan_Application__c` (proposed, with View All read or a narrow `without sharing` lookup) | GET status still works after the application is reassigned to a Loan Officer at submission |
| External Credential principal access `Core_Banking` (proposed) | If the Integration User is the running user for the event triggers (LAMS-067) |

**External Client App** — Setup → External Client App Manager → New

| Setting | Value |
| --- | --- |
| Name / API name | *LAMS Integration* / `LAMS_Integration` (proposed) |
| Distribution state | Local |
| Enable OAuth | On; callback URL `https://localhost/callback` (required field, not used by this flow) |
| OAuth scopes | *Manage user data via APIs (api)* only |
| Flow enablement | **Enable Client Credentials Flow** = on; all other flows off |
| Security | Require secret for web server flow (default); require PKCE off (not used) |
| Policies → OAuth | Client Credentials Flow → **Run As** = Integration User |
| Policies → App | Permitted users: admin-approved; select permission set `LAMS_Integration` |
| Session timeout | 2 hours (proposed) |

**Token request** (always the My Domain URL, never `login.salesforce.com`):

```
POST https://<mydomain>.my.salesforce.com/services/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<consumer key>&client_secret=<consumer secret>
```

Response 200: `{"access_token":"00D…","instance_url":"https://<mydomain>.my.salesforce.com","token_type":"Bearer",…}` — no refresh token. Calls then send `Authorization: Bearer <access_token>`.

**Source control:** commit `ExternalClientApplication`, `ExtlClntAppOauthSettings` and `ExtlClntAppOauthConfigurablePolicies`. Do **not** commit the consumer key or secret; if `ExtlClntAppGlobalOauthSettings` is retrieved, add it to `.forceignore`.

**Manual, not deployable:** consumer key/secret, the Run As user selection (org-specific username), the permission set licence assignment. Record them in the README "Manual steps" list.

## Steps

1. Open the Integration User (LAMS-029); assign the *Salesforce API Integration* permission set licence, then `LAMS_Integration`:
   `sf org assign permset --name LAMS_Integration --on-behalf-of <integration username>`
2. Create the External Client App with the settings above; under Policies set the Run As user and permitted permission set.
3. Copy the consumer key and secret (Settings → OAuth Settings → Consumer Key and Secret) into your local Postman environment only (*current value*, never *initial value*).
4. In Postman, request a token with the call above; then `GET {{instanceUrl}}/services/oauth2/userinfo` and check `preferred_username` is the Integration User.
5. Retrieve: `sf project retrieve start --metadata ExternalClientApplication:LAMS_Integration ExtlClntAppOauthSettings ExtlClntAppOauthConfigurablePolicies PermissionSet:LAMS_Integration`
6. Check nothing secret is staged: `git diff --cached | findstr /i "secret consumerKey"` returns nothing.
7. Add the manual steps to the README.
8. Commit: `feat(security): Integration User and LAMS Integration external client app [LAMS-068]`.

## Learn

- **Client credentials flow:** a server-to-server token with no user login and no refresh token; every call runs as the configured Run As user, so that user's permissions are the API's permissions.
- **External Client Apps** are the newer, packageable replacement for connected apps; settings are split into the app, its OAuth settings and admin-controlled policies.
- **Salesforce Integration licence:** API only, cannot log in to the UI, and needs the *Salesforce API Integration* permission set licence before it can hold custom object permissions.
- An OAuth access token is also a session Id, so the same token works as the `sessionId` in the SOAP header (LAMS-071).

## Done when

- [ ] A Postman token request returns 200 with an `access_token` for the Integration User
- [ ] `userinfo` shows the Integration User, and Setup → Login History shows the login with login type *OAuth Client Credentials* (or similar) for that user
- [ ] The token request with a wrong secret returns 400 `invalid_client`
- [ ] App metadata and the updated `LAMS_Integration` are in source; no consumer key or secret in the repo
- [ ] README lists the manual steps (secret, Run As user, permission set licence)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §4 non-business actors, §11 profiles and `LAMS_Integration`, §16 Dealer/DSA, Payment Gateway and Legacy rows, §19 Secrets and Not in source, BR-06, BR-41, BR-67
