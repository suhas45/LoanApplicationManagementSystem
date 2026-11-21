# LAMS-030 · lamsSettings LWC + LamsSettingsController + tests

**Milestone:** [M04 – Security](README.md) · **Size:** M (2–5h) · **Delivers:** BR-74

**Depends on:** LAMS-017, LAMS-019, LAMS-020, LAMS-021, LAMS-024, LAMS-025, LAMS-029

## Goal

The Credit Head flips toggles and edits thresholds on a *LAMS Settings* app page. The page's Apex checks the custom permission `LAMS_Manage_Settings` before it updates the org default, so only the Credit Head changes settings (BR-74, BR-79), and she doesn't need the broad setup rights hierarchy custom settings normally require (appendix #17). This is the "Credit Head can flip a toggle" check in §20 step 3.

## Build

**Apex `LamsSettingsController`**: `public with sharing class`.

| Member | Signature | Behaviour |
| --- | --- | --- |
| Inner DTO | `public class SettingField { @AuraEnabled public String apiName; label; helpText; type; Object value; }` | `type` is the `Schema.DisplayType` name: `BOOLEAN`, `CURRENCY`, `DOUBLE`, `PERCENT` |
| Read | `@AuraEnabled public static List<SettingField> getSettings()` | Checks the permission. Returns every custom field of LAMS_Settings__c from `Schema.SObjectType.LAMS_Settings__c.fields.getMap()`, with label and help text from describe and the value from `LAMS_Settings__c.getOrgDefaults()`. Booleans first, then the rest, each sorted by label |
| Save | `@AuraEnabled public static List<SettingField> saveSettings(Map<String, Object> changes)` | Checks the permission. Rejects keys that aren't custom, updateable fields. Converts each value by DisplayType (Boolean, or Decimal for number types) and rejects negative numbers. Puts the values on the org-default row, creating it with `SetupOwnerId = UserInfo.getOrganizationId()` if missing. Runs `upsert`, calls `FeatureToggle.reset()` and returns `getSettings()` |
| Guard | `private static void requireManageSettings()` | `if (!FeatureManagement.checkPermission('LAMS_Manage_Settings'))` → throw |
| Errors | `private static AuraHandledException error(String msg)` | `new AuraHandledException(msg)` **plus `setMessage(msg)`**, using `LAMS_Settings_No_Permission` or `LAMS_Settings_Invalid_Value` |

- The DML runs in system mode. Don't use `AccessLevel.USER_MODE` here, because the custom permission is the guard. Before build, confirm that a non-admin Credit Head can save through this class (§11 note "Validate the exact permission needed in your org").
- Only the org default is edited. Pilot `Agentforce_Enabled__c` user overrides stay in Setup → Custom Settings → Manage.

**LWC `lamsSettings`**

| File | Content |
| --- | --- |
| `lamsSettings.js-meta.xml` | `isExposed` true, target `lightning__AppPage`, `masterLabel` *LAMS Settings* |
| `lamsSettings.html` | `lightning-card` titled with `LAMS_Settings_Title`. Two sections, `LAMS_Settings_Features` (one `lightning-input type="toggle"` per BOOLEAN) and `LAMS_Settings_Thresholds` (`lightning-input type="number"`, `formatter="currency"` for CURRENCY, `step="0.01"` for PERCENT). `field-level-help` = helpText. Save button `LAMS_Settings_Save`, disabled until something changes |
| `lamsSettings.js` | Calls `getSettings` imperatively in `connectedCallback`. Tracks only changed values in a map. On Save, calls `saveSettings({ changes })`, shows a success toast `LAMS_Settings_Saved` and re-renders from the result. On error, shows an error toast with `error.body.message` |

All text comes from custom labels (LAMS-021) or field describe, with no literals. The UI API doesn't support custom settings, which is why labels come from Apex describe and not `getObjectInfo`.

**Page and access**

| Item | Value |
| --- | --- |
| Lightning App Page | *LAMS Settings* (`LAMS_Settings`), one region with `lamsSettings` |
| Tab | `LAMS_Settings` (Lightning Page tab), added to the LAMS app |
| LAMS_Policy_Admin | Add Apex class access `LamsSettingsController` and tab visibility `LAMS_Settings` = Visible |

**Apex test `LamsSettingsControllerTest`**

| Test | Assert |
| --- | --- |
| `creditHeadReadsSettings` | User with LAMS_Policy_Admin gets all 22 fields with the stored values |
| `creditHeadTogglesOnAndOff` | `saveSettings({'Auto_Approve_Enabled__c' => true})` → org default true and `FeatureToggle.isAutoApproveEnabled()` true. Then false → false |
| `creditHeadUpdatesThreshold` | `Offer_Validity_Days__c` 15 → 10 is saved |
| `createsOrgDefaultWhenMissing` | With no row, a save creates one with `SetupOwnerId` = org Id |
| `userWithoutPermissionIsBlocked` | User without the permission: both methods throw `AuraHandledException` whose message equals `System.Label.LAMS_Settings_No_Permission`. Row unchanged |
| `unknownFieldRejected` | Key `Name` or `Foo__c` → `LAMS_Settings_Invalid_Value` |
| `negativeNumberRejected` | `Auto_Approve_Max_Amount__c = -1` → `LAMS_Settings_Invalid_Value` |

Create the users and the `PermissionSetAssignment` for LAMS_Policy_Admin in `@TestSetup` inside `System.runAs(new User(Id = UserInfo.getUserId()))`.

**Jest (proposed):** `__tests__/lamsSettings.test.js`. Mock `getSettings` and assert one toggle per BOOLEAN. Change a toggle and assert that `saveSettings` is called with only that key.

## Steps

1. `sf apex generate class --name LamsSettingsController --output-dir force-app/main/default/classes` and the same for `LamsSettingsControllerTest`.
2. `sf lightning generate component --name lamsSettings --type lwc --output-dir force-app/main/default/lwc`.
3. Build the class, tests and component. Deploy: `sf project deploy start --metadata ApexClass:LamsSettingsController ApexClass:LamsSettingsControllerTest LightningComponentBundle:lamsSettings`.
4. Run: `sf apex run test --class-names LamsSettingsControllerTest --code-coverage --result-format human --wait 10`. Optionally run `npm run test:unit` for Jest.
5. Create the App Page and tab in Lightning App Builder, add the tab to the LAMS app, and update LAMS_Policy_Admin.
6. Retrieve: `sf project retrieve start --metadata FlexiPage:LAMS_Settings CustomTab:LAMS_Settings CustomApplication:LAMS PermissionSet:LAMS_Policy_Admin ApexClass:LamsSettingsController`
7. Demo: as the admin (who acts as Credit Head in the `Lams` org, LAMS-029), turn Auto Approve on and save. Query `SELECT Auto_Approve_Enabled__c FROM LAMS_Settings__c`. Turn it off again.
8. Commit: `feat(lwc): lamsSettings page and LamsSettingsController with tests [LAMS-030]`.

## Learn

- **Custom permissions** are named switches checked in code (`FeatureManagement.checkPermission`), formulas (`$Permission`) and flows. They give a business user a narrow right instead of a broad system permission.
- **`AuraHandledException` gotcha:** in Apex tests `getMessage()` returns "Script-thrown exception" unless you also call `setMessage()`. Always set it, both so the LWC shows the right text and so tests can assert the label.
- **Hierarchy settings in the UI API:** Lightning Data Service and `getObjectInfo` don't support custom settings, so a settings screen needs an Apex controller.
- **Audit:** check Setup → View Setup Audit Trail after a save. If changes made through Apex don't appear there (the BRD assumes they do, §11 Audit), log it in the Parking lot.

## Done when

- [ ] Logged in as the Credit Head, the LAMS Settings tab shows 13 toggles and 9 thresholds (including Callback_Rate_Limit__c, used by LAMS-097) with their labels and help text, and a saved change is visible in `LAMS_Settings__c` (§20 step 3)
- [ ] A Credit Manager and an Operations Officer don't see the tab, and calling the controller without LAMS_Manage_Settings returns the `LAMS_Settings_No_Permission` message
- [ ] `LamsSettingsControllerTest` covers toggle on and off, threshold change, missing row, no permission, unknown field and negative value; coverage of the class ≥ 90%
- [ ] No hardcoded user-facing text in the LWC or the class
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Editing settings, Custom permissions, Permission sets (LAMS_Policy_Admin), Audit; §12; §14 LamsSettingsController; §15 lamsSettings; §20 step 3; appendix #17; BR-74, BR-79, NFR-10
