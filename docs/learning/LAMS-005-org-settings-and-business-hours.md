# LAMS-005 · Learning notes: org settings, Digital Experiences, languages and business hours

**Date:** 2026-11-24 · **Milestone:** M01 – Org and repo · **Spec:** [005-enable-digital-experiences-translation.md](../milestones/M01-org-and-repo/005-enable-digital-experiences-translation.md)

## 1. What this work item was about

Turning on org-wide switches that later milestones need:

| Switch | Needed for |
| --- | --- |
| Digital Experiences | The borrower portal (M10) |
| End-user and platform-only languages, and Hindi as a translation language | Hindi labels and picklists (BR-54, NFR-12) |
| Business Hours `LAMS IST` | Escalations and reminders that count Indian working days (BR-55, BR-56) |
| Indian locale, time zone and INR | `₹` amounts and IST times everywhere |

This is also the **first item that put metadata in `force-app`**.

## 2. What was built

```
force-app/main/default/settings/
├── BusinessHours.settings-meta.xml   Default + LAMS IST
├── Communities.settings-meta.xml     enableNetworksEnabled = true
└── Language.settings-meta.xml        enableEndUserLanguages, enablePlatformLanguages = true
```

**LAMS IST** in XML:

```xml
<businessHours>
    <active>true</active>
    <default>false</default>
    <mondayStartTime>09:30:00.000Z</mondayStartTime>
    <mondayEndTime>18:00:00.000Z</mondayEndTime>
    ... (Tuesday to Saturday the same)
    <name>LAMS IST</name>
    <timeZoneId>Asia/Kolkata</timeZoneId>
</businessHours>
```

Things to notice:
- **The `Z` doesn't mean UTC here.** Times are read in the record's own `timeZoneId`, so `09:30:00.000Z` means 09:30 India time.
- **Sunday has no start or end time.** A missing day means "closed". `00:00`–`00:00` would mean open 24 hours, which is what the `Default` record uses for every day.
- **`default = false`.** Later items pick `LAMS IST` by name, and the org's `Default` record stays as it is.

## 3. How it was deployed

```bash
# 1. Look at the current settings first (read-only, into a scratch folder)
sf project retrieve start --metadata "Settings:BusinessHours" "Settings:Language" --output-dir <scratch>

# 2. Edit the XML in force-app, then check without saving
sf project deploy start --dry-run --source-dir force-app/main/default/settings --target-org Lams

# 3. Real deploy
sf project deploy start --source-dir force-app/main/default/settings --target-org Lams

# 4. Retrieve back, so the files hold exactly what the org stored
sf project retrieve start --metadata "Settings:BusinessHours" "Settings:Language" "Settings:Communities" --target-org Lams
```

**Why retrieve after deploying?** `Communities.settings-meta.xml` was deployed with **one** flag. Settings files can be partial: only the fields you include change. The retrieve brought back the full file with every flag, which is now the true picture of the org in source.

**Verification:**

```bash
sf data query --query "SELECT Name, IsActive, IsDefault, TimeZoneSidKey, MondayStartTime, SundayStartTime FROM BusinessHours"
sf sobject list --sobject all | grep '^Network$'   # exists only once Digital Experiences is on
```

## 4. What can't be deployed, and why it's a manual step

| Setting | Why it's manual |
| --- | --- |
| Company Information (time zone, locale, currency) | Stored on the `Organization` record, which neither the data API nor the Metadata API can change |
| Translation Language Settings (Hindi + translator) | No metadata type for it |

These go in the *Manual steps* section of `ORG_NOTES.md`, so a new org can be rebuilt: deploy `force-app`, then do the listed clicks.

## 5. Salesforce concepts practised

- **Settings metadata.** Most Setup checkboxes are fields in a `*Settings` type (`Settings:Communities`, `Settings:Language`, …). That's how org configuration ends up in git.
- **Some switches are one-way.** Digital Experiences can't be turned off again, so turn on irreversible features only when the design needs them.
- **Business hours** are used by escalation rules, entitlements, approval reminders and Apex `BusinessHours.add(bhId, start, millis)`. The record's time zone makes "2 business days" mean Indian working days for every user.
- **Translation Workbench** translates metadata (labels, picklist values, field names), not record data or email bodies. Email templates need one template per language (LAMS-047).
- **Org default vs user settings.** Your user was already on IST, but scheduled jobs, the Automated Process user and new users take the **org** default. That's why the org time zone must change too.
- **Currency locale** can only be changed while multi-currency is off, and should be set before records with amounts exist.

## 6. Checks (Done when)

- [x] Digital Experiences enabled (`Network` object exists)
- [x] Business Hours `LAMS IST` active, Mon–Sat 09:30–18:00, Sunday closed, in `force-app`
- [x] Manual steps listed in `ORG_NOTES.md`
- [ ] Company Information: time zone Asia/Kolkata, locale English (India), INR (manual)
- [ ] Hindi active in Translation Language Settings with you as translator (manual)
- [ ] A test Account's Annual Revenue shows `₹`
