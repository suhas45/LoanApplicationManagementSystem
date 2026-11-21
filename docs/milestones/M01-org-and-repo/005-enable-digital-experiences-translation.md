# LAMS-005 · Enable Digital Experiences, Translation Workbench (Hindi), Business Hours "LAMS IST"

**Milestone:** [M01 – Org and repo](README.md) · **Size:** S (≤ 2h) · **Delivers:** §19

**Depends on:** LAMS-003 (CLI connected, to retrieve the settings)

## Goal

The org-level switches that later milestones rely on are on: Digital Experiences for the borrower portal (BR-59 – BR-61), Hindi as a translation language (BR-54, NFR-12) and the "LAMS IST" business hours used by escalations and approval reminders (BR-55, BR-56, assumption A5). The org also uses Indian locale, time zone and rupees so every amount displays as ₹.

## Build

**Company Information (proposed; the BRD states ₹ and IST but no org setting)**

| Setting | Value |
| --- | --- |
| Default Locale | English (India) |
| Default Language | English |
| Default Time Zone | (GMT+05:30) India Standard Time (Asia/Kolkata). **In the `Lams` org this is still America/Los_Angeles** (LAMS-002); change it here. Your user is already Asia/Kolkata, but scheduled jobs, the Automated Process user and new users take the org default |
| Currency Locale | English (India) – INR. Multi-currency stays off (out of scope, §3) |
| Your admin user | Same locale and time zone |

**Digital Experiences** — Setup → Digital Experiences → Settings: *Enable Digital Experiences*. The domain is fixed by My Domain (`<mydomain>.develop.my.site.com` style). No site yet; the site is LAMS-074. This cannot be turned off again.

**Languages and Translation Workbench**

| Setting | Value |
| --- | --- |
| Setup → Language Settings | *Enable End User Languages* and *Enable Platform-Only Languages* on, so Hindi (`hi`) can be chosen whatever its support tier in this release |
| Setup → Translation Language Settings | Add **Hindi**, *Active* checked, translator = your admin user |

**Business Hours** — Setup → Business Hours → New.

| Field | Value |
| --- | --- |
| Business Hours Name | `LAMS IST` |
| Active | Checked |
| Use these business hours as the default | Unchecked (proposed; LAMS-078 and LAMS-064 reference it by name) |
| Time Zone | (GMT+05:30) India Standard Time (Asia/Kolkata) |
| Monday – Saturday | 09:30 – 18:00 |
| Sunday | No Hours |
| Holidays | None for now (proposed) |

Change Data Capture, also on the §19 checklist, is switched on in LAMS-014 once Loan__c and Payment__c exist.

## Steps

1. Edit Company Information and your user record with the locale values.
2. Enable Digital Experiences.
3. Turn on the language settings and add Hindi in Translation Language Settings.
4. Create Business Hours `LAMS IST`.
5. Retrieve what is metadata:
   `sf project retrieve start --metadata Settings:BusinessHours Settings:Language`
   Open `force-app/main/default/settings/BusinessHours.settings-meta.xml` and check it holds `LAMS IST` with the right times.
6. Under *Manual steps* in [ORG_NOTES.md](ORG_NOTES.md), list: Company Information locale and currency, Enable Digital Experiences, Translation Language Settings (Hindi, translator). These are not deployed from source.
7. Run `sf project deploy start --dry-run --source-dir force-app` to make sure the retrieved settings deploy.
8. Commit: `chore(org): Digital Experiences, Hindi translation, LAMS IST business hours [LAMS-005]`.

## Learn

- **Settings metadata** (`Settings:BusinessHours`, `Settings:Language`) carries org preferences in source; some switches (Digital Experiences, Company Information) are one-time manual steps and belong in the README (§19 "Not in source").
- **Business hours** are used by escalation rules, entitlements and Apex `BusinessHours.add()`; a time zone on the record makes "2 business days" mean Indian working days whatever the user's time zone.
- **Translation Workbench** only translates metadata (custom labels, picklist values, field labels); email templates need one template per language (LAMS-047).
- Currency locale can be changed only while multi-currency is off; set it before records with amounts exist.

## Done when

- [ ] A test currency field shows `₹` (for example the Annual Revenue field on a test Account), and times show in IST
- [ ] Company Information shows Default Time Zone Asia/Kolkata (no longer America/Los_Angeles)
- [ ] Setup → Digital Experiences → Settings shows Digital Experiences enabled with the site domain
- [ ] Translation Language Settings lists Hindi as Active with you as translator
- [ ] Business Hours `LAMS IST` is active with Mon–Sat 09:30–18:00 and Sunday no hours, and is in `force-app` source
- [ ] Manual steps are listed in [ORG_NOTES.md](ORG_NOTES.md)
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Org setup checklist; §13.5 Business Hours "LAMS IST"; §15 portal; §8 A5, D4; BR-54, BR-55, BR-56, NFR-12
