# LAMS-020 · Post-deploy script that sets settings defaults

**Milestone:** [M03 – Configuration](README.md) · **Size:** S (≤ 2h) · **Delivers:** §19

**Depends on:** LAMS-017

## Goal

One anonymous Apex script creates the LAMS_Settings__c org default with the §12 values. Any org built from this repo then has working toggles straight after `sf project deploy start`, because custom setting values are data and don't deploy (§19). The script is safe to re-run and doesn't undo the Credit Head's changes.

## Build

**File `scripts/apex/set-lams-settings-defaults.apex`**

| Behaviour | Rule |
| --- | --- |
| Target | The org-default row: `SetupOwnerId = UserInfo.getOrganizationId()` |
| First run (no row) | Insert the row with every value below |
| Re-run (row exists) | Fill only **blank** thresholds; leave checkboxes and set values alone |
| Full reset | A `Boolean RESET = false;` line at the top; set it to `true` to overwrite every field with the defaults |
| Output | `System.debug` of `created` / `updated` and the final values |
| User and profile rows | Not touched (pilot `Agentforce_Enabled__c` overrides are set by hand) |

Default values (from §12):

| Field | Value | Field | Value |
| --- | --- | --- | --- |
| Auto_Approve_Enabled__c | false | Portal_Enabled__c | true |
| Auto_Approve_Max_Amount__c | 500000 | Agentforce_Enabled__c | false |
| Second_Approval_Threshold__c | 2500000 | Data_Cloud_Enabled__c | false |
| Secured_Review_Enabled__c | true | Offer_Validity_Days__c | 15 |
| Bureau_Mock_Mode__c | true | Application_Expiry_Days__c | 30 |
| KYC_Mock_Mode__c | true | KYC_Reuse_Months__c | 12 |
| Payout_Mock_Mode__c | true | Refer_Score_Tolerance__c | 20 |
| SMS_Enabled__c | false | Refer_Ratio_Tolerance__c | 5 |
| Partner_API_Enabled__c | false | Approval_Reminder_Days__c | 2 |
| Event_Publishing_Enabled__c | true | Core_Banking_Sync_Enabled__c | false |
| Late_Fees_Enabled__c | true | | |

Shape of the script:

```apex
Boolean RESET = false;
LAMS_Settings__c s = LAMS_Settings__c.getOrgDefaults();
Boolean isNew = (s == null || s.Id == null);
if (isNew) { s = new LAMS_Settings__c(SetupOwnerId = UserInfo.getOrganizationId()); }
Map<String, Object> defaults = new Map<String, Object>{
    'Auto_Approve_Enabled__c' => false,
    'Auto_Approve_Max_Amount__c' => 500000
    // … every field in the table above
};
for (String f : defaults.keySet()) {
    if (isNew || RESET || s.get(f) == null) { s.put(f, defaults.get(f)); }
}
upsert s;
System.debug((isNew ? 'created ' : 'updated ') + s);
```

## Steps

1. Write the script. Keep the defaults map in the same order as §12 so a reviewer can compare line by line.
2. Deploy the metadata first (`sf project deploy start`), then run: `sf apex run --file scripts/apex/set-lams-settings-defaults.apex`. Add `--target-org <alias>` for a non-default org.
3. Check: `sf data query --query "SELECT SetupOwnerId, Auto_Approve_Enabled__c, Second_Approval_Threshold__c, Offer_Validity_Days__c, Refer_Ratio_Tolerance__c FROM LAMS_Settings__c"`. Expect one row whose SetupOwnerId starts with `00D`.
4. Prove a toggle is readable from Flow (milestone exit criterion): open a new Autolaunched Flow and add a Text formula `IF({!$Setup.LAMS_Settings__c.Auto_Approve_Enabled__c}, "on", "off")`. Add an Assignment that uses it, then **Debug**. Expect "off". Don't save the flow.
5. Prove it from Apex: `echo "System.debug(FeatureToggle.isAutoApproveEnabled());" | sf apex run`.
6. Add the run command to the setup notes you'll write in LAMS-092 ("after every fresh deploy, run …").
7. Commit: `chore(config): post-deploy script for LAMS_Settings__c org defaults [LAMS-020]`.

## Learn

- **Data vs metadata:** `sf project deploy start` moves the custom setting *definition*, not its rows. Settings rows, seed data (LAMS-016) and users need scripts or data plans.
- `getOrgDefaults()` returns an object with a null `Id` when no org row exists. That lets one script handle both insert and update with `upsert`.
- An idempotent script (safe to run twice) only fills gaps by default. A blind overwrite after every deploy would silently undo toggles the Credit Head changed, which goes against O5.
- CI (LAMS-004) runs a validate-only deploy, which never runs this script. Tests insert their own settings (LAMS-019).

## Done when

- [ ] `sf apex run --file scripts/apex/set-lams-settings-defaults.apex` succeeds on the org and creates exactly one org-default row with the §12 values
- [ ] Running it a second time after flipping `Late_Fees_Enabled__c` to false leaves it false; running with `RESET = true` sets it back to true
- [ ] A Flow debug shows `$Setup.LAMS_Settings__c.Auto_Approve_Enabled__c`, and anonymous Apex prints `FeatureToggle.isAutoApproveEnabled()` (M03 exit criterion)
- [ ] The script is committed under `scripts/apex/`
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §19 Source control and deployment ("Settings data"), §12 defaults table and "How toggles are read", §20 step 3 done-check, O5, BR-79 – BR-81
