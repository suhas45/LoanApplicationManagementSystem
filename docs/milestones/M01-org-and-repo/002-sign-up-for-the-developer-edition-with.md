# LAMS-002 · Sign up for the Developer Edition with Agentforce and Data Cloud; confirm Experience Cloud, Orchestration, Messaging; record limits in `ORG_NOTES.md`

**Milestone:** [M01 – Org and repo](README.md) · **Size:** S (≤ 2h) · **Delivers:** C1, D1

**Depends on:** LAMS-001 (the repo exists, so [ORG_NOTES.md](ORG_NOTES.md) can be committed)

## Goal

One Developer Edition org has every platform feature the BRD needs (Experience Cloud, Flow Orchestration, Messaging, Agentforce, Data Cloud; dependency D1), and its limits are written down before any build starts (constraint C1). Gaps found now become fallbacks rather than late surprises in M10–M12.

## Build

**Org.** Use the free *Developer Edition with Agentforce and Data Cloud* sign-up on developer.salesforce.com. A plain Developer Edition (the link in the root `README.md`) or a 30-day trial is the wrong org: it lacks Data Cloud, and a trial expires.

| Sign-up field | Value |
| --- | --- |
| Username | Email-shaped and unique across all of Salesforce, e.g. `<you>.lams@dev.example` (proposed). It does not have to be a real mailbox |
| Email | A real inbox; the activation link and verification codes go there |
| My Domain (if asked) | Already set in the existing org (CLI alias `Lams`); record the real My Domain URL in [ORG_NOTES.md](ORG_NOTES.md) |

**The org already exists (CLI alias `Lams`).** These facts are known; copy them into [ORG_NOTES.md](ORG_NOTES.md) and check the rest of this item against them.

| Fact | Value |
| --- | --- |
| Edition | Developer Edition; Agentforce, Data Cloud (starter) and Messaging licences present |
| User licences | 2 free full **Salesforce**, 6 **Salesforce Platform**, 1 **Salesforce Integration**, 5 **Customer Community Login**. The extra admin user "OrgFarm EPIC" already holds one full Salesforce licence |
| Storage | 5 MB data, 20 MB files |
| Email | 15 single emails per day (Developer Edition limit) |
| Time zone | Your user is Asia/Kolkata, but the **org default is still America/Los_Angeles**; fixed in LAMS-005 |
| API version | 68.0 |

**Feature check.** For each row, record *Yes / No* and what you saw.

| Feature | Where to check | Needed by |
| --- | --- | --- |
| Experience Cloud | Setup → *Digital Experiences* → Settings page exists (do **not** enable yet; that is LAMS-005) | M10 portal (BR-59 – BR-61) |
| Flow Orchestration | Setup → Flows → *New Flow*: the *Record-Triggered Orchestration* and *Autolaunched Orchestration* types are listed | LAMS-050 (BR-20) |
| Messaging for In-App and Web | Setup → *Messaging Settings* → New Channel offers *Messaging for In-App and Web*; Setup → *Embedded Service Deployments* exists | LAMS-087 Borrower Assistant |
| Agentforce | Setup → *Einstein Setup* can be turned on; Setup → *Agentforce Agents* and *Prompt Builder* pages open | LAMS-085 – LAMS-087 (BR-75 – BR-77) |
| Data Cloud | App Launcher → *Data Cloud* app opens and *Data Cloud Setup* shows the org as provisioned. Newer releases call the product *Data 360* | LAMS-088, LAMS-089 (BR-78) |
| Change Data Capture | Setup → *Change Data Capture* page exists; note the number of entities allowed | LAMS-014 |
| Classic encryption | Field type *Text (Encrypted)* is offered on a test custom field (cancel without saving) | LAMS-012 (BR-72) |
| Marketing User | A user record offers the *Marketing User* checkbox (needed for the Credit Head to edit campaigns) | LAMS-029, M14 (BR-88) |

**Limits to record.** Compare each with what LAMS needs.

| Limit | Where | LAMS needs |
| --- | --- | --- |
| Data storage, file storage | Setup → *Storage Usage* | Seed and demo data only; 60,000-instalment volumes (NFR-01) are proven in Apex tests, not loaded |
| Salesforce user licences | Setup → *Company Information* → User Licenses | 6 staff logins + admin (§19). In this org: admin (acts as Credit Head) + Loan Officer 1 + Operations Officer 1 on Salesforce; Credit Manager, Loan Officer 2, Operations Officer 2 on Salesforce Platform (LAMS-029) |
| Salesforce Integration licence | Same | 1 Integration User (LAMS-068) |
| Customer Community Login licences | Same (User Licenses or Feature Licenses) | 2 portal borrowers (LAMS-029) |
| Dynamic dashboards | Salesforce Help, *Dynamic dashboard limits* (Developer Edition is documented as a small number, typically 3) | 2 (LAMS-081, LAMS-082) |
| Flow Orchestration runs | Setup → *Company Information* → Usage-based Entitlements (or *Digital Wallet*) | A few dozen demo runs |
| Einstein / Agentforce requests, Data Cloud credits | Setup → *Digital Wallet* (or Usage-based Entitlements) | Demo conversations and one Data Cloud refresh per day |
| API requests per 24 h | Setup → *Company Information* → API Requests, Last 24 Hours | CI deploys, Postman runs, mock callouts |
| Org expiry or inactivity policy | Sign-up confirmation email and Developer Edition terms | Log in at least monthly |

**File [ORG_NOTES.md](ORG_NOTES.md)** (in this milestone folder, `docs/milestones/M01-org-and-repo/`; create it if missing) with these sections:

1. *Org* — edition, Org ID, instance, My Domain URL, username (never the password or security token), sign-up date.
2. *Features* — the feature-check table above, filled in.
3. *Licences and limits* — the limits table with the numbers you found.
4. *Gaps and fallbacks* — each shortfall and what you will do instead (for example "only 2 free full Salesforce licences → the admin acts as Credit Head; Credit Manager, Loan Officer 2 and Operations Officer 2 on Salesforce Platform with no Lead, Campaign or Case access; Disputes go to the Credit Head queue"; "15 emails a day → point demo borrowers at your own inbox and test sparingly").
5. *Manual steps* — empty for now; later items (LAMS-005, LAMS-006) append to it.

## Steps

1. Sign up, activate from the email, set the password and a verification method (Salesforce Authenticator or an authenticator app; MFA is enforced on login).
2. Walk the feature-check table in Setup. Take a screenshot of anything that is *No*.
3. Walk the limits table and copy the numbers.
4. Write [ORG_NOTES.md](ORG_NOTES.md). Copy each gap into the [M01 parking lot](README.md#parking-lot) and link it from the BRD risk table if it changes the plan.
5. Optional, after LAMS-003: append `sf org list limits --target-org Lams` output (DataStorageMB, FileStorageMB, DailyApiRequests) to the notes.
6. Commit: `docs(org): record Developer Edition features and limits [LAMS-002]`.

## Learn

- **Editions decide features.** Developer Edition is free and permanent, but licences and storage are small; the Agentforce/Data Cloud variant adds AI and Data Cloud without a trial clock.
- **Licences are the hidden constraint.** Staff who work Cases need a full Salesforce licence (a Salesforce Platform licence has no Case access), and Developer Edition has few. Decide early which demo users are real logins and which are simulated.
- **Consumption-based features** (Agentforce, Data Cloud, Orchestration) draw on credits or run counts. Check usage in Setup before demos, not during them.
- Data storage counts about 2 KB per record whatever its size, so a 5 MB allowance means only a few thousand rows.
- **Platform licences** cover custom objects, Accounts, Contacts and activities, but not Leads, Campaigns, Cases or Opportunities. That is why this org's licence plan gives the two free full licences to the users who work Leads and Cases.

## Done when

- [ ] You can log in to the new org with MFA
- [ ] [ORG_NOTES.md](ORG_NOTES.md) exists, with every row of both tables filled (a number, *Yes*, or *No*)
- [ ] Every *No* or shortfall has a fallback in *Gaps and fallbacks* and an entry in the parking lot
- [ ] The file contains no password, security token or auth URL
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §8 D1, C1, C4; §19 Org setup checklist; §17 Agentforce and Data Cloud; §18 dynamic dashboard note; NFR-01
