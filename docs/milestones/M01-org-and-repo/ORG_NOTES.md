# Org notes – `Lams`

Facts about the development org. First checked on 2026-11-21; completed for LAMS-002 on 2026-11-23 with read-only CLI queries, a settings retrieve and one dry-run deploy (nothing saved). No passwords, tokens or auth URLs belong in this file.

## 1. Org

| Item | Value |
| --- | --- |
| Edition | Developer Edition with Agentforce and Data Cloud (not a sandbox, no trial expiry) |
| Org ID | `00Dak00001Pki8nEAB` |
| Instance | USA840 |
| My Domain URL | `https://orgfarm-3959145e9d-dev-ed.develop.my.salesforce.com` |
| Admin username | `suhas.vaddeman@agentforce.com` |
| Sign-up (org created) | 2026-11-02 |
| CLI alias | `Lams` (default `target-org` for this project, **Local** config in `.sf/config.json`, git-ignored). Checked 2026-11-23 (LAMS-003) |
| Login URL | `https://login.salesforce.com` (matches `sfdcLoginUrl` in `sfdx-project.json`) |
| API version | 68.0 in the org (`sf org display`) = `sourceApiVersion` in `sfdx-project.json`. `org-api-version` is not set and not needed: the CLI uses the org's version |
| CLI version | `@salesforce/cli/2.159.7` (Node 26.13.0), updated 2026-11-23 with `sf update stable` |
| CLI install | Windows installer at `C:\Program Files\sf` (self-updates into `%LOCALAPPDATA%\sf\client`). Update with `sf update`, **not** `npm install -g`; an npm copy would sit later on PATH and never be used |
| Org default time zone / locale | Asia/Kolkata, en_IN, INR (changed by hand in LAMS-005, checked 2026-11-27). Was America/Los_Angeles, en_US |
| Developer user time zone / locale | Asia/Kolkata, en_IN |
| Business hours | `Default` (24 h, America/Los_Angeles, org default) and **`LAMS IST`** (Asia/Kolkata, Mon–Sat 09:30–18:00, Sunday closed, not default), in source since LAMS-005 |
| Person Accounts | Not enabled, and will not be (BRD Appendix D1) |

Other orgs authorised on this machine (inkarp-DEV, inkarp-SIT, inkarp-UAT) are client sandboxes. **Never** pass `--target-org` with one of them from this project.

## 2. Features

| Feature | Present? | Evidence (2026-11-23) | Needed by |
| --- | --- | --- | --- |
| Experience Cloud | **Yes, enabled 2026-11-24** | 5 Customer Community Login licences; `CommunitiesSettings.enableNetworksEnabled = true` deployed in LAMS-005 (cannot be turned off); `Network` object now exists. No site yet (LAMS-074) | M10 portal (BR-59 – BR-61) |
| Flow Orchestration | **Yes** | `FlowOrchestrationInstance` / `FlowOrchestrationWorkItem` objects exist; flow `ProcessType` offers `Orchestrator`; entitlement *Maximum Orchestration Runs* = 600 per year | LAMS-050 (BR-20) |
| Messaging for In-App and Web | **Yes (capped)** | `MessagingChannel`, `MessagingSession`, `EmbeddedServiceDetail` objects exist; Enhanced Chat User (11) and Messaging User (6) licences; entitlement *Maximum Total Conversations for Messaging* = **10, once** | LAMS-087 Borrower Assistant |
| Agentforce | **Yes** | `EinsteinGptSettings.enableEinsteinGptPlatform = true`; Agentforce (Default), Agentforce Service Agent Builder/User, Einstein Prompt Templates licences; `BotDefinition` and `GenAiPlannerDefinition` objects exist; an `EinsteinServiceAgent User` already exists | LAMS-085 – LAMS-087 (BR-75 – BR-77) |
| Data Cloud | **Yes, licensed, not provisioned** | `Data Cloud` (`GenieDataPlatformStarterPsl`) licence, 2 assigned; Data Cloud entitlements present (3 connections, 45,000 profiles). But `CustomerDataPlatformSettings.enableCustomerDataPlatform = false`, no `DataSpace` object and no `__dlm` objects: Data Cloud Setup has not been run | LAMS-088, LAMS-089 (BR-78) |
| Change Data Capture | **Yes** | 169 `*ChangeEvent` entities available. Developer Edition allows 5 selected entities (Salesforce Help) | LAMS-014 |
| Classic encryption | **Yes** | Dry-run deploy of a test object with a `Text (Encrypted)` field succeeded; nothing was saved | LAMS-012 (BR-72) |
| Marketing User | **Yes** | `User.UserPermissionsMarketingUser` field exists | LAMS-029, M14 (BR-88) |
| Einstein Bots (classic) | No (off) | `BotSettings.enableBots = false`. Not needed; LAMS uses Agentforce agents | — |

## 3. Licences and limits

### User licences

| Licence | Total | Used | Free | LAMS plan |
| --- | --- | --- | --- | --- |
| Salesforce | 4 | 2 (developer admin, "OrgFarm EPIC" admin) | 2 | Admin acts as Credit Head; Loan Officer 1 and Operations Officer 1 take the 2 free licences |
| Salesforce Platform | 6 | 0 | 6 | Credit Manager, Loan Officer 2, Operations Officer 2 (no Lead, Campaign or Case access) |
| Salesforce Integration | 1 | 0 | 1 | 1 Integration User (LAMS-068) |
| Customer Community Login | 5 | 0 | 5 | 2 portal borrowers (LAMS-029) |

A Platform licence has no Lead, Campaign or Case access. The full user plan is in BRD §19 (licence plan).

### Limits

| Limit | Value in `Lams` | LAMS needs | OK? |
| --- | --- | --- | --- |
| Data storage | 5 MB (about 2,500 records at ~2 KB each) | Seed and demo data only; NFR-01 volumes proven in Apex tests | Yes, if demo data stays small |
| File storage | 20 MB | Small sample documents (under 1 MB each) | Yes |
| Dynamic dashboards | 3 (Developer Edition, Salesforce Help; not readable via API) | 2 (LAMS-081, LAMS-082) | Yes |
| Flow Orchestration runs | 600 per year | A few dozen demo runs | Yes |
| Messaging conversations | **10 in total (once, not per month)** | Borrower Assistant demo conversations | **Tight**, see gaps |
| Einstein / Agentforce requests | Not exposed via API; check Setup → *Digital Wallet* before demos | Demo conversations | Check before LAMS-085 |
| Data Cloud | 3 connections, 45,000 profiles, 20,000 segment publishes | 1 connection (CRM), a few hundred profiles, 1 refresh per day | Yes |
| Daily API requests | 15,000 per 24 h (450,000 per month) | CI deploys, Postman runs, mock callouts | Yes |
| Single emails per day | 15 (mass email 10) | Notification tests | Tight, see gaps |
| Daily async Apex executions | 250,000 | Batches, queueables | Yes |
| Hourly published platform events | 50,000 (10,000 delivered per day) | `Loan_Event__e` traffic | Yes |
| Permission sets | 1,500 (1,494 free) | 8 + groups | Yes |
| Org expiry | None (`TrialExpirationDate` is null) | Must survive the whole build | Yes. Inactive Developer Edition orgs can be locked, so log in at least monthly |

## 4. Gaps and fallbacks

| Gap | Fallback |
| --- | --- |
| Only 2 free full Salesforce licences | Licence plan in BRD §19; security tests run as non-admin users |
| Credit Manager cannot see Cases (Platform licence) | Dispute cases route to the Credit Head (admin) in this org |
| 5 MB data storage | Volumes (NFR-01) are proven in Apex tests, not with stored data; short-tenure demo loans; delete test data after demos |
| 15 single emails a day | Email deliverability stays "System email only" until notifications are tested; Apex tests never send email; test in small batches to your own inbox |
| **Data Cloud licensed but not provisioned** | Run Setup → *Data Cloud Setup* → *Get Started* well before M12 (provisioning can take an hour or more). If it fails, keep the Data Cloud toggle off and document the design in the README (BRD risk table) |
| **Messaging: 10 conversations in total** | Test the Borrower Assistant in Agent Builder / preview first; use real portal Messaging conversations only for the final demo recording (LAMS-087, LAMS-093) |
| CDC: 5 selected entities in Developer Edition | LAMS-014 selects only the entities the design needs (Loan__c, Loan_Application__c, Payment__c); stay at or under 5 |
| Agentforce request credits not visible via API | Check Setup → *Digital Wallet* before LAMS-085 and before each demo |

## 5. Manual steps

Clicks that cannot be deployed from source. Repeat them in any new org, after deploying `force-app`.

| # | Item | Where | Value |
| --- | --- | --- | --- |
| 1 | LAMS-005 | Setup → Company Information → Edit | Default Locale **English (India)**; Default Language English; Default Time Zone **(GMT+05:30) India Standard Time (Asia/Kolkata)**; Currency Locale **English (India) – INR**. Multi-currency stays off |
| 2 | LAMS-005 | Setup → Users → your user | Locale English (India), Time Zone Asia/Kolkata (already set in `Lams`) |
| 3 | LAMS-005 | Setup → Translation Language Settings → Add | Language **Hindi**, Active checked, Translators: your admin user. Needs `Language.settings` deployed first (end-user and platform languages on) |

Deployed from source instead of clicked (LAMS-005): Digital Experiences on (`Communities.settings`), end-user and platform-only languages on (`Language.settings`), Business Hours `LAMS IST` (`BusinessHours.settings`).
