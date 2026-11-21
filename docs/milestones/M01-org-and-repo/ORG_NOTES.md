# Org notes – `Lams`

Facts about the development org, checked on 2026-11-21 with read-only queries. No passwords, tokens or auth URLs belong in this file.

## Org

| Item | Value |
| --- | --- |
| CLI alias | `Lams` (default `target-org` for this project, set in `.sf/config.json`) |
| Edition | Developer Edition (not a sandbox) |
| Instance | USA840 |
| API version | 68.0 (matches `sfdx-project.json`) |
| Org default time zone / locale | America/Los_Angeles, en_US — **change to Asia/Kolkata, English (India), INR** (LAMS-005) |
| Developer user time zone / locale | Asia/Kolkata, en_IN |
| Person Accounts | Not enabled, and will not be (BRD Appendix D1) |

Other orgs authorised on this machine (inkarp-DEV, inkarp-SIT, inkarp-UAT) are client sandboxes. **Never** pass `--target-org` with one of them from this project.

## Features present

| Feature | Evidence | Needed for |
| --- | --- | --- |
| Agentforce | Agentforce Service Agent Builder/User, Prompt Templates, Copilot permission set licences | M12 |
| Data Cloud | Data Cloud starter (`GenieDataPlatformStarterPsl`), segments and activations licence | M12 |
| Messaging for In-App and Web | Embedded Service Messaging User licences (11) | Borrower Assistant (LAMS-087) |
| Experience Cloud | 5 Customer Community Login licences | M10 portal |
| Flow Orchestration, Translation Workbench, Digital Experiences | Check in Setup during LAMS-005 | M07, M03, M10 |

## Licences

| Licence | Total | Used | Free |
| --- | --- | --- | --- |
| Salesforce | 4 | 2 (developer admin, "OrgFarm EPIC" admin) | 2 |
| Salesforce Platform | 6 | 0 | 6 |
| Salesforce Integration | 1 | 0 | 1 |
| Customer Community Login | 5 | 0 | 5 |

A Platform licence has no Lead, Campaign or Case access. The user plan that fits is in BRD §19 (licence plan): the developer admin acts as Credit Head, Loan Officer 1 and Operations Officer 1 get the two full licences, and the Credit Manager, Loan Officer 2 and Operations Officer 2 use Platform licences.

## Limits

| Limit | Value | How we live with it |
| --- | --- | --- |
| Data storage | 5 MB (about 2,500 records) | Keep demo data small; prefer short-tenure demo loans (a 30-year loan is 360 EMI rows); delete test data after demos |
| File storage | 20 MB | Small sample documents only (under 1 MB each) |
| Single emails per day | 15 | Email deliverability stays "System email only" until notifications are tested; Apex tests never send email |
| Daily API requests | 15,000 | Enough for CI and Postman runs |
| Daily async Apex executions | 250,000 | Enough |
| Hourly published platform events | 50,000 | Enough |

## Gaps and fallbacks

| Gap | Fallback |
| --- | --- |
| Only 2 free full licences | Licence plan in BRD §19; security tests run as non-admin users |
| Credit Manager cannot see Cases (Platform licence) | Dispute cases route to the Credit Head (admin) in this org |
| 5 MB data storage | Volumes (NFR-01) are proven in Apex tests, not with stored data |
| 15 emails a day | Test notifications in small batches |
