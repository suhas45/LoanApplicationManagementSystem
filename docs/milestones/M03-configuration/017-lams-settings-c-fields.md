# LAMS-017 · LAMS_Settings__c fields

**Milestone:** [M03 – Configuration](README.md) · **Size:** S (≤ 2h) · **Delivers:** §12

**Depends on:** M02 done

## Goal

One hierarchy custom setting holds every feature switch and business threshold, so the Credit Head can change behaviour without a release (BR-79 – BR-81, NFR-13). Apex reads it only through FeatureToggle (LAMS-019). Flows and validation rules read it through `$Setup.LAMS_Settings__c`.

## Build

**Custom setting `LAMS_Settings__c`**: label *LAMS Settings*, Setting Type **Hierarchy**, Visibility **Public**, description "LAMS feature toggles and thresholds (BRD §12). Values are data: run scripts/apex/set-lams-settings-defaults.apex after deploy."

| Field (API name) | Type | Default | Scope | Help text (proposed) |
| --- | --- | --- | --- | --- |
| Auto_Approve_Enabled__c | Checkbox | false | Org | Auto-approve small Personal Loans (BR-27) |
| Auto_Approve_Max_Amount__c | Currency(16,2) | 500000 | Org | Highest amount that can be auto-approved (BR-81) |
| Second_Approval_Threshold__c | Currency(16,2) | 2500000 | Org | Above this, the Credit Head must also approve (BR-22) |
| Secured_Review_Enabled__c | Checkbox | true | Org | Field verification for products that require it (BR-20) |
| Bureau_Mock_Mode__c | Checkbox | true | Org | Credit bureau returns a mock response (BR-69) |
| KYC_Mock_Mode__c | Checkbox | true | Org | KYC provider returns a mock response (BR-69) |
| Payout_Mock_Mode__c | Checkbox | true | Org | Payout service returns a mock response (BR-69) |
| SMS_Enabled__c | Checkbox | false | Org | Send SMS alongside email (BR-53) |
| Partner_API_Enabled__c | Checkbox | false | Org | Accept partner submissions; off = HTTP 503 (BR-06) |
| Event_Publishing_Enabled__c | Checkbox | true | Org | Publish Loan_Event__e (BR-68) |
| Core_Banking_Sync_Enabled__c | Checkbox | false | Org | Post disbursements and payments to core banking (BR-38, BR-47) |
| Late_Fees_Enabled__c | Checkbox | true | Org | Nightly late fee after grace days (BR-48) |
| Portal_Enabled__c | Checkbox | true | Org | Borrower portal open; off = maintenance message (BR-61) |
| Agentforce_Enabled__c | Checkbox | false | User or profile override allowed | AI assistants on for this user (pilot) (BR-75) |
| Data_Cloud_Enabled__c | Checkbox | false | Org | Customer insights write-back (BR-78) |
| Offer_Validity_Days__c | Number(3,0) | 15 | Org | Days an offer stays open (BR-28, BR-30) |
| Application_Expiry_Days__c | Number(3,0) | 30 | Org | Days with no activity before an undecided application expires (BR-31) |
| KYC_Reuse_Months__c | Number(3,0) | 12 | Org | A KYC verified within this many months is reused (BR-10) |
| Refer_Score_Tolerance__c | Number(3,0) | 20 | Org | Score points below minimum that still give Refer (BR-12) |
| Refer_Ratio_Tolerance__c | Percent(3,2) | 5 | Org | EMI-to-income or LTV points over the limit that still give Refer (BR-12) |
| Approval_Reminder_Days__c | Number(2,0) | 2 | Org | Business days before an approver is reminded (BR-55) |

That is 21 fields: 13 checkboxes and 8 thresholds. Make none of them required. Checkboxes can't be null. Thresholds can be blank until the script in LAMS-020 fills them.

The "Scope" column is a rule for how values are read and set, not a field property. Only `Agentforce_Enabled__c` may have profile- or user-level rows. Every other field is set at the org default only.

**Not here:** `Orchestration_Enabled__c` was renamed to `Secured_Review_Enabled__c` in v2, and per-integration `Active__c` was removed from Integration_Setting__mdt (LAMS-018). Each integration has one switch, in this setting.

## Steps

1. Setup → Custom Settings → New: label *LAMS Settings*, object name `LAMS_Settings`, Hierarchy, Public.
2. Add the 21 fields with the types and defaults above. Put the BR reference in each field's Description.
3. Retrieve: `sf project retrieve start --metadata CustomObject:LAMS_Settings__c`. Check that `force-app/main/default/objects/LAMS_Settings__c/LAMS_Settings__c.object-meta.xml` contains `<customSettingsType>Hierarchy</customSettingsType>` and a `fields/` folder with 21 files.
4. Check the deploy: `sf project deploy start --metadata CustomObject:LAMS_Settings__c --dry-run`.
5. Commit: `feat(config): LAMS_Settings__c hierarchy custom setting [LAMS-017]`.

## Learn

- **Hierarchy vs list custom settings:** a hierarchy setting resolves a value as user → profile → org default. That is why system toggles must be read from the org default (LAMS-019). Platform-event and async code runs as the Automated Process user, where user overrides don't apply (BRD constraint C3).
- **Custom settings vs custom metadata:** custom setting *values* are data. They don't deploy with the code, and Apex tests can't see them without inserting them. Custom metadata records do deploy, which is why endpoints live in Integration_Setting__mdt (BR-82).
- **Field defaults apply only when a record is created.** Changing a default later doesn't update the existing org-default row. Re-run the script in LAMS-020 instead.
- Custom settings allow only a few field types (Checkbox, Currency, Date, Date/Time, Email, Number, Percent, Phone, Text, Text Area, URL). There are no picklists or lookups.

## Done when

- [ ] `LAMS_Settings__c` exists as a Hierarchy setting with exactly the 21 fields above, and the types and defaults match the table
- [ ] Setup → Custom Settings → LAMS Settings → Manage offers **New** at the org-default level and at the profile/user level
- [ ] The object and fields are in `force-app/` and `sf project deploy start --dry-run` succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §12 Configuration and feature toggles (field table), §8 constraint C3, §10.11, §19 (settings data), BR-79 – BR-81, NFR-13
