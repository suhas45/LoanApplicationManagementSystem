# LAMS-040 · Named + External Credentials (5) pointing at mocks

**Milestone:** [M06 – Origination](README.md) · **Size:** S (≤ 2h) · **Delivers:** §16

**Depends on:** LAMS-006 (public mock endpoints), LAMS-018 (Integration_Setting__mdt.Named_Credential__c values), LAMS-024 (permission sets that get principal access)

## Goal

Each outbound integration is reached through `callout:<Name>`, with the endpoint in a Named Credential and the secret only in an External Credential filled in the org by hand (§16, §19 Secrets). Endpoints move between orgs with the code (BR-82); no URL or key appears in Apex.

## Build

**Five pairs** — Named Credential and External Credential share the name, matching Integration_Setting__mdt.Named_Credential__c:

| Name | Style | URL (from LAMS-006) | Used by |
| --- | --- | --- | --- |
| `Credit_Bureau` | REST | Beeceptor/Postman mock base URL for the bureau | CreditBureauService (LAMS-041) |
| `KYC_Service` | SOAP | Mock base URL returning the KYC SOAP envelope | KycService (LAMS-042) |
| `Payout_Service` | REST | Payout mock | PayoutService (LAMS-056) |
| `SMS_Gateway` | REST | SMS mock | SmsService (LAMS-063) |
| `Core_Banking` | REST | Core banking mock | CoreBankingSyncQueueable (LAMS-067) |

**External Credential (each)** — Authentication Protocol **Custom**; one Named Principal `Mock` (proposed) with an authentication parameter `ApiKey`. The value is typed in Setup after deploy and never committed.

**Named Credential (each)** — Type **Secured Endpoint**; URL = mock base URL only (paths come from Integration_Setting__mdt.Path__c); External Credential = same name; **Generate Authorization Header** off; **Allow Formulas in HTTP Header** on; Custom Header `x-api-key` = `{!$Credential.Credit_Bureau.ApiKey}` (use each credential's own name). Callout options: no client certificate.

**Principal access** — callouts run as the user whose transaction enqueued them, so every user type that can trigger a call needs *External Credential Principal Access* to `Mock` in a permission set:

| Permission set (LAMS-024) | Credentials | Why |
| --- | --- | --- |
| LAMS_Loan_Officer | Credit_Bureau, KYC_Service | Branch submissions start the bureau → KYC chain |
| LAMS_Borrower_Portal | Credit_Bureau, KYC_Service | Portal submissions run the chain as the borrower (proposed; see note) |
| LAMS_Integration | Credit_Bureau, KYC_Service | Partner API submissions |
| LAMS_Credit | Credit_Bureau, KYC_Service, SMS_Gateway | Overrides and approvals that re-run checks or notify |
| LAMS_Operations | Payout_Service, Core_Banking, SMS_Gateway | Disbursement and servicing |

Note (proposed): giving portal users principal access only lets Apex call the mock on their behalf; they cannot read the key. Revisit if the chain is later moved to run as a dedicated user.

**Not needed:** Remote Site Settings (Named Credentials replace them).

## Steps

1. In Setup → Named Credentials → External Credentials, create the five External Credentials with principal `Mock` and parameter `ApiKey`.
2. Create the five Named Credentials pointing at the LAMS-006 URLs, with the `x-api-key` header formula.
3. Edit the permission sets above → External Credential Principal Access → add the principals.
4. Enter the ApiKey values (any value the mock accepts) on each principal.
5. Smoke-test from Anonymous Apex (mock mode is irrelevant here — this calls the endpoint directly):
   ```apex
   HttpRequest r = new HttpRequest();
   r.setEndpoint('callout:Credit_Bureau/health'); r.setMethod('GET');
   System.debug(new Http().send(r).getStatusCode());
   ```
6. Retrieve: `sf project retrieve start --metadata NamedCredential:Credit_Bureau NamedCredential:KYC_Service NamedCredential:Payout_Service NamedCredential:SMS_Gateway NamedCredential:Core_Banking ExternalCredential:Credit_Bureau ExternalCredential:KYC_Service ExternalCredential:Payout_Service ExternalCredential:SMS_Gateway ExternalCredential:Core_Banking PermissionSet`
7. Check no secret value is in the retrieved XML before committing.
8. Commit: `feat(integration): named and external credentials for 5 mocks [LAMS-040]`.

## Learn

- **Named vs External Credential:** the Named Credential holds *where* (URL, options); the External Credential holds *how to authenticate* and *who may use it* (principals granted through permission sets).
- **Secrets never deploy:** parameter values are not in metadata; a new org needs them typed in (document it in the README, LAMS-092).
- **`callout:Name/path`** makes Apex environment-independent; a sandbox or another DE org just points the Named Credential elsewhere (BR-82).
- A user without principal access gets a callout error even though the code is right — a classic cause of "works for admin, fails for the portal".

## Done when

- [ ] Five Named Credentials and five External Credentials exist in the org and in `force-app/` source, names matching Integration_Setting__mdt
- [ ] Anonymous Apex callout through each Named Credential reaches its mock and returns the expected status
- [ ] The same callout run as a Loan Officer test user (Login As) succeeds for Credit_Bureau
- [ ] No API key or URL hardcoded in Apex; no secret in the repo (`git grep` for the key returns nothing)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §16 Integrations, §10.11 Integration\_Setting\_\_mdt, §19 Secrets, BR-65, BR-82, D2
