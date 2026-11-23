# LAMS-002 · Learning notes: checking an org's features and limits

**Date:** 2026-11-23 · **Milestone:** M01 – Org and repo · **Spec:** [002-sign-up-for-the-developer-edition-with.md](../milestones/M01-org-and-repo/002-sign-up-for-the-developer-edition-with.md) · **Output:** [ORG_NOTES.md](../milestones/M01-org-and-repo/ORG_NOTES.md)

## 1. What this work item was about

Before building anything, check that the org can run everything the BRD needs and write down its limits. A Developer Edition org is free, but it has small licence counts, small storage and capped usage-based features. Finding a gap in M01 costs one line in a notes file. Finding it in M12 means redesigning work you have already built.

Nothing was deployed. This item produces knowledge, not metadata.

## 2. What changed in the repo

| File | Change |
| --- | --- |
| `docs/milestones/M01-org-and-repo/ORG_NOTES.md` | Rewritten into the 5 required sections: Org, Features, Licences and limits, Gaps and fallbacks, Manual steps. Every row filled |
| `docs/milestones/M01-org-and-repo/README.md` | LAMS-002 ticked; 4 parking-lot entries added |
| `docs/learning/LAMS-002-org-features-and-limits.md` | This note |

## 3. Key findings

- **Two features are licensed but not switched on:** Experience Cloud (planned for LAMS-005) and **Data Cloud**, which still needs *Data Cloud Setup → Get Started*. Provisioning can take a while, so do it well before M12.
- **Messaging is capped at 10 conversations in total**, and the cap does not reset. Test the Borrower Assistant in preview and save real conversations for the demo.
- **Orchestration: 600 runs a year.** That is plenty for demos.
- **CDC: 5 selected entities** in Developer Edition, so LAMS-014 has to pick carefully.
- **Classic encryption works.** A dry-run deploy with an Encrypted Text field succeeded.

## 4. How the checks were done (and what you can reuse)

Most checks in the spec say "look in Setup". Almost all of them can also be answered from the CLI, which is faster, repeatable and leaves evidence in your terminal.

### a) Org facts: SOQL on `Organization`

```bash
sf data query --target-org Lams --query "SELECT Name, OrganizationType, InstanceName, IsSandbox, CreatedDate, TimeZoneSidKey, TrialExpirationDate FROM Organization"
```

`TrialExpirationDate = null` tells you the org does not expire.

### b) Licences: `UserLicense` and `PermissionSetLicense`

```bash
sf data query --target-org Lams --query "SELECT Name, TotalLicenses, UsedLicenses FROM UserLicense WHERE TotalLicenses > 0"
sf data query --target-org Lams --query "SELECT MasterLabel, TotalLicenses, UsedLicenses FROM PermissionSetLicense WHERE TotalLicenses > 0"
```

- A **user licence** is the base seat a user is created on (Salesforce, Salesforce Platform, Customer Community Login). Each user has exactly one.
- A **permission set licence (PSL)** is an add-on that unlocks a feature for a user who already has a seat (Agentforce, Data Cloud, Messaging). A user can hold many.

### c) Limits: `sf org list limits`

```bash
sf org list limits --target-org Lams
```

This returns the same data as the REST `/limits` endpoint: storage, daily API requests, emails, async Apex and platform events.

### d) Usage-based entitlements: `TenantUsageEntitlement`

```bash
sf data query --target-org Lams --query "SELECT MasterLabel, CurrentAmountAllowed, Frequency FROM TenantUsageEntitlement"
```

This query found the Orchestration (600/year) and **Messaging (10 total)** caps. Both are hard to find in Setup.

### e) Is a feature present? Look for its objects

When a feature is enabled, its sObjects appear in the schema:

```bash
sf sobject list --sobject all --target-org Lams
```

| Feature | Object that proves it |
| --- | --- |
| Orchestration | `FlowOrchestrationInstance` |
| Messaging | `MessagingChannel`, `EmbeddedServiceDetail` |
| Agentforce | `BotDefinition`, `GenAiPlannerDefinition` |
| Experience Cloud (enabled) | `Network` (absent here, because it is not enabled yet) |
| Data Cloud (provisioned) | `DataSpace`, `*__dlm` objects (absent here) |
| CDC | `AccountChangeEvent` and the other `*ChangeEvent` objects |

To check a single field, describe the object: `sf sobject describe --sobject User` shows `UserPermissionsMarketingUser`, which proves the Marketing User checkbox exists.

### f) Is a feature turned on? Retrieve its Settings metadata

Every Setup switch is stored in a `Settings` metadata type. Retrieve it into a temporary folder (not into `force-app`) and read the XML:

```bash
sf project retrieve start --target-org Lams --metadata "Settings:Communities" "Settings:CustomerDataPlatform" "Settings:EinsteinGpt" --output-dir /tmp/settings
```

| Setting | Value found | Meaning |
| --- | --- | --- |
| `CommunitiesSettings.enableNetworksEnabled` | false | Digital Experiences not enabled yet |
| `CustomerDataPlatformSettings.enableCustomerDataPlatform` | false | Data Cloud not provisioned |
| `EinsteinGptSettings.enableEinsteinGptPlatform` | true | Generative AI is on |

These same files are how features get turned on from source later. LAMS-005 can deploy `Communities.settings-meta.xml` with `enableNetworksEnabled = true` and skip the Setup clicks.

### g) Can I create X? Run a dry-run deploy

To test "is Encrypted Text available?" without touching the org, build a throwaway object with one `EncryptedText` field in a scratch folder and run:

```bash
sf project deploy start --dry-run --target-org Lams --source-dir force-app
```

`--dry-run` makes Salesforce validate everything and then roll back, so nothing is saved. Success means the feature works. Use this whenever you want to know whether metadata is valid before committing to it.

## 5. Salesforce concepts practised

- **Editions decide features.** "Developer Edition with Agentforce and Data Cloud" is a different provisioning from a plain Developer Edition, even though both report `OrganizationType = Developer Edition`.
- **Licensed is not the same as enabled.** Data Cloud and Experience Cloud are both paid for here but still switched off. Always check the setting, not just the licence.
- **Platform licences** cover custom objects, Accounts and Contacts, but not Leads, Campaigns, Cases or Opportunities. That is why LAMS's licence plan gives the two free full licences to the people who work Leads and Cases.
- **Data storage counts about 2 KB per record**, whatever the record's size, so 5 MB is only about 2,500 records. A 30-year loan's EMI schedule alone is 360 rows.
- **Consumption caps** (Orchestration runs, Messaging conversations, AI credits) are separate from per-day governor limits. Some reset yearly, and some (`Frequency = Once`) never reset.

## 6. Safety habits used

- Every command passed `--target-org Lams` explicitly, because client sandboxes are also authorised on this machine.
- `sf org display` was not used, since it prints an access token. `sf org list` redacts tokens.
- `ORG_NOTES.md` holds no password, token or auth URL. It does hold the admin username and My Domain URL, as the spec asks. Consider removing them before the repo goes public (LAMS-093).

## 7. Still to do by hand

- Confirm you can log in to the org with MFA (the first *Done when* check).
- Optional: open Setup → *Digital Wallet* and note the Agentforce/Einstein credit balance in `ORG_NOTES.md`.
