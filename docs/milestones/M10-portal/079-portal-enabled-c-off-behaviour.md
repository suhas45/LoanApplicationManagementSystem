# LAMS-079 · Portal_Enabled__c off behaviour

**Milestone:** [M10 – Portal](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-61

**Depends on:** LAMS-017 (`Portal_Enabled__c`), LAMS-019 (FeatureToggle), LAMS-030 (lamsSettings LWC to flip it), LAMS-035 (New Loan Application flow), LAMS-052 (Respond to Offer, Withdraw Application flows), LAMS-076 (portal pages)

## Goal

The Credit Head can switch the portal off without a release: borrowers see a maintenance message and portal flows exit cleanly, while staff using the same flows in Lightning are unaffected (BR-61, BR-79, BR-80, NFR-13).

## Build

**LWC `portalStatusBanner`** (proposed name) — targets `lightningCommunity__Page`, `lightningCommunity__Default`; placed at the top of Home (slot reserved in LAMS-076).

| Item | Spec |
| --- | --- |
| Apex | `public with sharing class PortalStatusController { @AuraEnabled public static Boolean isPortalEnabled() }` → `FeatureToggle` org default for `Portal_Enabled__c` |
| Call | Imperative and **not** `cacheable=true`, so a flip shows on the next page load (NFR-13) |
| Off | Shows a `role="alert"` banner with label `LAMS_Portal_Maintenance_Message` (proposed, EN/HI); the Home tiles still render, but every flow behind them exits |
| On | Renders nothing |

**Flow guard** — first element in each flow used by the portal:

| Flow | Decision *Portal off for this user?* | Off path |
| --- | --- | --- |
| New_Loan_Application | `NOT(ISBLANK({!$User.ContactId}))` AND `{!$Setup.LAMS_Settings__c.Portal_Enabled__c} = false` | Screen with `LAMS_Portal_Maintenance_Message`, then end (no record created) |
| Respond_to_Offer | same | same |
| Withdraw_Application | same | same |

The `$User.ContactId` check is what keeps staff unaffected: internal users have no Contact, so the guard never fires for them.

**Service requests (proposed):** the portal Create Case Form is not a flow; add a Case validation rule `Portal_Closed` — `AND(ISNEW(), NOT(ISBLANK($User.ContactId)), NOT($Setup.LAMS_Settings__c.Portal_Enabled__c))` with the maintenance label — so a borrower cannot raise a request through the portal while it is off. Staff and the phone channel still can.

**Not in scope:** deactivating the site (Workspaces → Administration → Settings → Deactivate) is the manual emergency switch; record it in the README.

## Steps

1. Build `PortalStatusController` + `PortalStatusControllerTest` (toggle on → true, off → false).
2. Build `portalStatusBanner` with a Jest test for both states; deploy and place it on Home; publish.
3. Add the guard decision to the three flows; save new versions and activate.
4. Add the `Portal_Closed` validation rule (proposed) and its label.
5. As the Credit Head, switch *Portal enabled* off in lamsSettings. As a borrower: Home shows the banner, Apply shows the message and creates nothing, Respond to Offer exits. As a Loan Officer: New Loan Application still works in Lightning.
6. Switch it back on; the banner disappears on refresh.
7. Retrieve: `sf project retrieve start --metadata ApexClass:PortalStatusController LightningComponentBundle:portalStatusBanner Flow ValidationRule CustomLabels ExperienceBundle`
8. Commit: `feat(portal): Portal_Enabled__c maintenance mode [LAMS-079]`.

## Learn

- **One switch, two readers:** Apex reads the org default through FeatureToggle; flows and validation rules read `$Setup.LAMS_Settings__c`. Both see a change in the next transaction, with no deployment (NFR-13).
- **Cacheable Apex** results can be served from the client cache; for toggles that must take effect immediately, call imperatively.
- **Clean fallback (BR-80):** a switched-off feature should explain itself and stop before any DML, not throw an error halfway through.
- Using `$User.ContactId` to tell portal users from staff lets one flow serve both channels.

## Done when

- [ ] With `Portal_Enabled__c` off, the portal Home shows the maintenance message in the borrower's language
- [ ] With it off, Apply, Respond to Offer and Withdraw exit with the message and create or change nothing
- [ ] With it off, a Loan Officer runs New Loan Application in Lightning normally (BR-61)
- [ ] Switching it back on restores the portal without a deployment
- [ ] `PortalStatusControllerTest` (≥ 90%, on and off) and the banner Jest test pass
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §15 Portal paragraph (maintenance message, flows exit), §12 Portal_Enabled__c and How toggles are read, §13.2 flows, BR-61, BR-79, BR-80, NFR-13
