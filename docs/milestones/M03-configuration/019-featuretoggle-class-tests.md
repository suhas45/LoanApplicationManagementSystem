# LAMS-019 · FeatureToggle class + tests

**Milestone:** [M03 – Configuration](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-79

**Depends on:** LAMS-017; LAMS-021 for the label `LAMS_Error_Settings_Missing` (or create that one label now)

## Goal

`FeatureToggle` is the only Apex class that reads LAMS_Settings__c (BR-79, NFR-09). It reads system toggles from the org default, so they behave the same for every user, including the Automated Process user (C3). Only the user-scoped `Agentforce_Enabled__c` is read through the hierarchy. A switched-off feature then fails cleanly to its manual fallback (BR-80).

## Build

**Class `FeatureToggle`**: `public inherited sharing class`, all members `static`.

| Member | Returns | Reads |
| --- | --- | --- |
| `isAutoApproveEnabled()` | Boolean | `getOrgDefaults().Auto_Approve_Enabled__c` |
| `isSecuredReviewEnabled()` | Boolean | `Secured_Review_Enabled__c` |
| `isBureauMockMode()` | Boolean | `Bureau_Mock_Mode__c` |
| `isKycMockMode()` | Boolean | `KYC_Mock_Mode__c` |
| `isPayoutMockMode()` | Boolean | `Payout_Mock_Mode__c` |
| `isSmsEnabled()` | Boolean | `SMS_Enabled__c` |
| `isPartnerApiEnabled()` | Boolean | `Partner_API_Enabled__c` |
| `isEventPublishingEnabled()` | Boolean | `Event_Publishing_Enabled__c` |
| `isCoreBankingSyncEnabled()` | Boolean | `Core_Banking_Sync_Enabled__c` |
| `isLateFeesEnabled()` | Boolean | `Late_Fees_Enabled__c` |
| `isPortalEnabled()` | Boolean | `Portal_Enabled__c` |
| `isDataCloudEnabled()` | Boolean | `Data_Cloud_Enabled__c` |
| `isMockMode(String integrationName)` (proposed) | Boolean | Maps the Integration_Setting__mdt DeveloperName: `Credit_Bureau` → Bureau, `KYC` → KYC, `Payout` → Payout. Any other name → false |
| `isAgentforceEnabled()` | Boolean | **`LAMS_Settings__c.getInstance()`** (current user, hierarchy) |
| `isAgentforceEnabled(Id userId)` | Boolean | **`LAMS_Settings__c.getInstance(userId)`** |
| `autoApproveMaxAmount()` | Decimal | `Auto_Approve_Max_Amount__c` |
| `secondApprovalThreshold()` | Decimal | `Second_Approval_Threshold__c` |
| `offerValidityDays()` | Integer | `Offer_Validity_Days__c` |
| `applicationExpiryDays()` | Integer | `Application_Expiry_Days__c` |
| `kycReuseMonths()` | Integer | `KYC_Reuse_Months__c` |
| `referScoreTolerance()` | Integer | `Refer_Score_Tolerance__c` |
| `referRatioTolerance()` | Decimal | `Refer_Ratio_Tolerance__c` |
| `approvalReminderDays()` | Integer | `Approval_Reminder_Days__c` |
| `callbackRateLimit()` | Integer | `Callback_Rate_Limit__c` (proposed; portal callback requests per mobile in 24 hours, read by CallbackRequestController in LAMS-097) |
| `reset()` | void | Clears the cache. Call it after updating settings in the same transaction (LAMS-030, tests) |
| `SettingsMissingException` | inner class | Thrown by threshold getters when the value is blank |

Rules:

- Cache the org default once per transaction in `private static LAMS_Settings__c orgSettings`. A new transaction always re-reads, which meets NFR-13.
- Boolean getters return `value == true`. A missing org-default row reads as **off**, which is the safe manual fallback (BR-80).
- Threshold getters **never fall back to a hardcoded number** (NFR-09). If the value is null, throw `SettingsMissingException` with `System.Label.LAMS_Error_Settings_Missing`.
- No other class may call `LAMS_Settings__c.getOrgDefaults()` / `getInstance()`. Flows and validation rules use `$Setup.LAMS_Settings__c` instead.

**Test class `FeatureToggleTest`** (`@IsTest`):

| Test | Arrange | Assert |
| --- | --- | --- |
| `systemTogglesOn` | Org default with all 12 system checkboxes true | Every `is…()` returns true |
| `systemTogglesOff` | Org default with all false | Every `is…()` returns false |
| `noOrgDefaultMeansOff` | No settings row | Boolean getters return false; `autoApproveMaxAmount()` throws `SettingsMissingException` |
| `thresholdsReturnValues` | Org default with §12 defaults | Each threshold getter returns the stored value |
| `userOverrideIgnoredForSystemToggles` | Org default `Auto_Approve_Enabled__c = false`; user-level row for a test user with it true | Under `System.runAs(user)`, `isAutoApproveEnabled()` is **false** (this is the v1 bug fix) |
| `agentforceUserOverride` | Org default `Agentforce_Enabled__c = false`; user-level row true for user A | `isAgentforceEnabled(userA.Id)` true, `isAgentforceEnabled(userB.Id)` false; under `runAs(userA)` `isAgentforceEnabled()` true |
| `isMockModeMapsNames` | Bureau on, KYC off, Payout on | `isMockMode('Credit_Bureau')` true, `('KYC')` false, `('SMS')` false |
| `resetRereads` | Read, update the row, `reset()`, read again | The second read returns the new value |

Insert the org default with `SetupOwnerId = UserInfo.getOrganizationId()`. Insert a user-level row with `SetupOwnerId = user.Id`. Call `FeatureToggle.reset()` after each insert.

## Steps

1. `sf apex generate class --name FeatureToggle --output-dir force-app/main/default/classes`, and the same for `FeatureToggleTest`.
2. Write the class and tests to the spec above.
3. Deploy and run: `sf project deploy start --metadata ApexClass:FeatureToggle ApexClass:FeatureToggleTest` then `sf apex run test --class-names FeatureToggleTest --code-coverage --result-format human --wait 10`.
4. Smoke test in the org: `echo "System.debug(FeatureToggle.isAutoApproveEnabled());" | sf apex run` (after LAMS-020 sets the defaults).
5. Commit: `feat(apex): FeatureToggle reader for LAMS_Settings__c with tests [LAMS-019]`.

## Learn

- **`getOrgDefaults()` vs `getInstance()`:** `getOrgDefaults()` always returns the org-level row. `getInstance()` merges user → profile → org for the *running* user. Async jobs and platform-event triggers run as the Automated Process user, so a user override silently doesn't apply there. That is why system toggles use org defaults only (BRD §12, appendix #16).
- **Custom setting data is invisible to tests.** Each test inserts the rows it needs, which is why "toggle on" and "toggle off" are easy to cover (NFR-10).
- `$Setup.LAMS_Settings__c.X` in a Flow or validation rule resolves through the hierarchy for the running user, like `getInstance()`. Keep user and profile rows for `Agentforce_Enabled__c` only, so the two readers never disagree.
- Static variables live for one transaction, so a static cache is safe and still picks up a change in the next transaction.

## Done when

- [ ] `FeatureToggle` exposes every getter in the table; no other class references `LAMS_Settings__c.getOrgDefaults()` or `getInstance()`
- [ ] `FeatureToggleTest` covers on, off, missing row, user override ignored, and Agentforce user override; all pass
- [ ] Coverage of `FeatureToggle` ≥ 90%
- [ ] Anonymous Apex prints the toggle value from the org
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §12 "How toggles are read", §14 FeatureToggle row and Tests, §8 constraint C3, appendix #16, BR-79, BR-80, NFR-09, NFR-10, NFR-13
