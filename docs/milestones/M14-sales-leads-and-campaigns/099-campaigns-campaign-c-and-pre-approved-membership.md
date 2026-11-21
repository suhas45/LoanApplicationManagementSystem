# LAMS-099 · Campaign types and member statuses, Loan_Application__c.Campaign__c, pre-approved membership and Applied status flows

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** M (2–5h) · **Delivers:** BR-88, AC-18

**Depends on:** LAMS-098 (LeadConversionService and `latestCampaignByLead`), LAMS-097 (CallbackRequestController and the Web-to-Lead form, for lead attribution), LAMS-038 (Application_Submitted flow, element 10 placeholder), LAMS-035 (New_Loan_Application flow), LAMS-008 (Contact.Pre_Approved__c), LAMS-024 (Campaign create/edit on LAMS_Policy_Admin; Campaign read on LAMS_Sales_Access), LAMS-026 (Campaign OWD Public Read Only), LAMS-029 (Marketing User on the Credit Head), LAMS-015 (application layouts and record pages)

## Goal

The Credit Head runs campaigns such as a pre-approved top-up offer. Every lead and every application records the campaign that produced it (BR-88). A borrower whose Pre_Approved__c becomes true joins the active Pre-approved Top-up campaign automatically, and only once. When they submit an application, it carries that campaign and their member status becomes *Applied*. Salesforce's campaign influence is built on Opportunities, which LAMS doesn't use, so campaign results come from `Loan_Application__c.Campaign__c` (§10.12, C5). This item completes **AC-18** except the report count, which LAMS-100 checks.

## Build

**Campaign setup** (standard object)

| Item | Value |
| --- | --- |
| Type picklist (Object Manager → Campaign → Type) | Pre-approved Top-up, Seasonal Offer, Partner Drive. Deactivate the standard values (Conference, Webinar, Trade Show, …) |
| Member statuses (per campaign) | **Sent** (default, not responded), **Responded** (responded), **Applied** (responded). Salesforce creates Sent and Responded on every new campaign; Applied is added by the flow below |
| OWD | Public Read Only internal (LAMS-026; confirm only) |
| Who edits | Users with LAMS_Policy_Admin (Campaign create/edit, LAMS-024) **and** the Marketing User checkbox. In `Lams`, that is the admin user acting as Credit Head (LAMS_Credit_Head_Group + Marketing User); a permission set can't grant Marketing User |
| LAMS app | Add the **Campaigns** navigation item; Campaign page layout gets the *Loan Applications* related list (below) |

**Flow `Campaign_Default_Member_Statuses`** (proposed): record-triggered on Campaign, after save, **created**. Create Records CampaignMemberStatus: CampaignId = `{!$Record.Id}`, Label `Applied`, HasResponded true, IsDefault false, SortOrder 3. Without this, the Submitted flow can't set *Applied* on a new campaign. If your org's Flow Builder doesn't offer CampaignMemberStatus, add *Applied* by hand under each campaign's *Advanced Setup* and record that in the README.

**Field `Loan_Application__c.Campaign__c`** (§10.12)

| Property | Value |
| --- | --- |
| Type | Lookup(Campaign); child relationship `Loan_Applications`; related list label *Loan Applications*; on Campaign delete: clear the value |
| Lookup filter (proposed, optional) | `Campaign: Active equals True`, so new selections pick only running campaigns |
| Layouts | All four application layouts and their Dynamic Forms record pages (LAMS-015): Application section, after Channel. Not on the portal layout |
| FLS (added to the existing sets; the field is on the application, so it goes in the application sets, BRD v2.3 D6) | Edit: LAMS_Loan_Officer. Read: LAMS_Credit. None: LAMS_Borrower_Portal, LAMS_Operations (proposed). The flows below set it in system context |

**Lead conversion (BR-88, "every application")**: in `LeadConversionService.createDraftApplications` (LAMS-098) set `app.Campaign__c = campaignByLead.get(lead.Id)` from the `latestCampaignByLead` map already built there. Add to `LeadConversionServiceTest`: a lead that belongs to two campaigns → the application gets the more recent one; a lead with none → blank.

**Leads record their campaign (BR-88, "every lead")**: through Campaign Members

| Source | How |
| --- | --- |
| Officer | *Add to Campaign* on the lead (Campaign History related list, LAMS-095), by a LAMS_Sales_Access holder (Lead edit + Campaign read). If your org also asks for Marketing User to add members, let the admin (Credit Head) add them instead and note it in the README |
| Web-to-Lead (LAMS-097) | Regenerate the form with a hidden **Campaign** field (`Campaign_ID` = the campaign's Id) and **Member Status** (`member_status` = `Responded`). Keep one form file per campaign, for example `web/enquiry-topup.html` (proposed). The Id is org-specific, like the rest of the form |
| Portal callback (proposed) | Add `Id campaignId` to `CallbackRequestController.CallbackRequest`. The LWC reads it from the page URL state `c__campaign` (`CurrentPageReference`). After the Lead insert, when the Id belongs to an active Campaign, insert `CampaignMember(LeadId, CampaignId, Status = 'Responded')`; an unknown or inactive Id is ignored silently (never an error to the guest). Add two tests: an active campaign → one member; a bogus Id → Lead saved, no member |
| Imported lists | LeadSource = *Campaign*, plus *Add to Campaign* after the import |

**Flow `Pre_Approved_Campaign_Membership`** (§13.6): record-triggered on **Contact**, after save, created or updated. Condition `Pre_Approved__c` Equals true; **only when a record is updated to meet the condition requirements**. LAMS-089's Data Cloud enrichment writes Contact.Pre_Approved__c. Until M12, set it by hand for the demo.

| # | Element | Details |
| --- | --- | --- |
| 1 | Get Records *Active top-up* | Campaign where `IsActive = true` AND `Type = Pre-approved Top-up`, sort StartDate descending, first record |
| 2 | Decision *Found?* | No → end (no campaign running is not an error) |
| 3 | Get Records *Existing member* | CampaignMember where CampaignId = campaign Id AND ContactId = `{!$Record.Id}` |
| 4 | Decision *Already a member?* | Yes → end ("once", BR-88) |
| 5 | Create Records | CampaignMember: CampaignId, ContactId = `{!$Record.Id}`, Status `Sent` |
| Fault | On 5 | Connector to the end. A membership problem must never fail the Data Cloud write-back or a user's Contact save |

The platform also refuses a second CampaignMember for the same Contact and Campaign. Element 4 makes "once" explicit, so the flip true → false → true does nothing.

**Flow change: `Application_Submitted` (LAMS-038)**: add after element 9

| # | Element | Details |
| --- | --- | --- |
| 10a | *Campaign from membership* (**proposed**; AC-18 needs a portal or branch application from a pre-approved borrower to "carry that campaign", and nobody else sets it) | Decision `{!$Record.Campaign__c}` is blank → Get Records CampaignMember where ContactId = `{!$Record.Borrower__c}` AND Status ≠ Applied, sort CreatedDate descending, first → Get Records Campaign where Id = member's CampaignId AND IsActive = true → found: Update Records `$Record` Campaign__c = that Id. Assign `varCampaignId` = `BLANKVALUE({!$Record.Campaign__c}, found Id)` |
| 10 | *Campaign Applied* (as specified in LAMS-038) | `varCampaignId` not blank → Get Records CampaignMember where CampaignId = `varCampaignId` AND ContactId = `{!$Record.Borrower__c}` → found: Update Records Status = `Applied`; none: Create Records CampaignMember with Status `Applied` (proposed) |
| Fault | On 10a and 10 | Connector to the end (proposed). Unlike the core elements of LAMS-038, campaign bookkeeping must never roll back a submission |

**Flow change: `New_Loan_Application` (LAMS-035)**: on the staff *Borrower* screen, add an optional lookup input for Campaign__c (label `LAMS_App_Campaign`, "Campaign (optional)" / "अभियान (वैकल्पिक)"), and write it in element 8. Portal users don't see it; element 10a covers them.

**Demo data** (keep it tiny: 5 MB storage). Script `scripts/apex/seed-campaigns.apex` (proposed) inserts one campaign *Pre-approved Top-up – Q4 2026*: Type Pre-approved Top-up, Status In Progress, IsActive true, StartDate today, EndDate today + 90. The status flow adds Applied. Run it with `sf apex run --file scripts/apex/seed-campaigns.apex --target-org Lams`.

**Tests `CampaignAutomationTest`** (proposed). Use the LAMS_Settings__c defaults and mocks from `ApplicationSubmittedFlowTest` (LAMS-038) so the submit path runs in tests. Insert campaigns as the admin; the test admin is a Marketing User.

| Test | Assert |
| --- | --- |
| `newCampaignGetsAppliedStatus` | Insert a Campaign → CampaignMemberStatus *Applied* (HasResponded true) exists alongside Sent and Responded |
| `preApprovedJoinsOnce` | `createBorrower`; set Pre_Approved__c true → 1 member, Status Sent. Set false, then true again → still 1 |
| `noActiveCampaignNoError` | Top-up campaign inactive → flag set, no member, no exception |
| `latestActiveCampaignChosen` | Two active top-up campaigns → member of the one with the later StartDate |
| `bulk200` | 200 borrowers flagged in one update → 200 members, no limit errors |
| `ac18_submittedApplicationCarriesCampaign` | Pre-approved member; Draft application with no Campaign__c; set Submitted → Campaign__c = the top-up campaign; member Status = Applied |
| `campaignSetWithoutMembership` | Officer-chosen Campaign__c, borrower not a member → after submit a member exists with Status Applied |
| `missingAppliedStatusDoesNotBlockSubmit` | Delete the campaign's Applied status, then submit → application reaches Document Review; member unchanged |
| `inactiveCampaignNotStamped` | Membership only in an inactive campaign → Campaign__c stays blank |

## Steps

1. Set the Campaign Type values; tick Marketing User on the admin (Credit Head) user if LAMS-029 hasn't.
2. Build and activate `Campaign_Default_Member_Statuses`, then run the seed script.
3. Create `Campaign__c`, add it to the layouts and record pages, set the FLS; add the Loan Applications related list to the Campaign layout; add Campaigns to the LAMS app.
4. Update LeadConversionService and its test; update CallbackRequestController, `callbackRequest` and their tests; regenerate the Web-to-Lead form with the campaign fields.
5. Build `Pre_Approved_Campaign_Membership`; add elements 10a and 10 to `Application_Submitted`; add the Campaign input to `New_Loan_Application`. Save new versions and activate them.
6. Write `CampaignAutomationTest`; run `sf apex run test --class-names CampaignAutomationTest --class-names LeadConversionServiceTest --class-names CallbackRequestControllerTest --class-names ApplicationSubmittedFlowTest --code-coverage --result-format human --wait 15 --target-org Lams`.
7. **AC-18 by hand.** On demo borrower Aarav Sharma's Contact (LAMS-016), tick Pre_Approved__c and check he is a *Sent* member of the top-up campaign. Untick and tick again: still one member. Log in to the portal as Aarav, apply for a Personal Loan top-up and submit. The application shows Campaign__c = the top-up campaign, and his member status is *Applied*. The report count is checked in LAMS-100.
8. Retrieve: `sf project retrieve start --metadata CustomObject:Campaign CustomField:Loan_Application__c.Campaign__c Flow:Campaign_Default_Member_Statuses Flow:Pre_Approved_Campaign_Membership Flow:Application_Submitted Flow:New_Loan_Application ApexClass:LeadConversionService ApexClass:CallbackRequestController ApexClass:CampaignAutomationTest LightningComponentBundle:callbackRequest Layout FlexiPage CustomApplication:LAMS CustomLabels Translations:hi PermissionSet:LAMS_Loan_Officer PermissionSet:LAMS_Credit --target-org Lams`
9. Commit: `feat(sales): campaigns, Campaign__c and pre-approved membership flows [LAMS-099]`.

## Learn

- **Campaign member statuses belong to each campaign**, not to the org. Every new campaign starts with Sent and Responded. *HasResponded* marks which statuses count as responses in campaign reports.
- **Campaign influence is Opportunity-based.** Influence and the campaign ROI fields roll up from Opportunities. A model with no Opportunities needs its own link, here Campaign__c on the application, and its own reports (LAMS-100).
- **Marketing User** is a checkbox on the User record, not a permission. Without it, even a System Administrator can't create or edit campaigns or import members.
- **One member per Contact per campaign:** the platform enforces it. A record-triggered flow on "updated to meet the condition" plus an existence check is the safe "join once" pattern, and the fault connector keeps a side effect from breaking the main save.

## Done when

- [ ] Campaign Type has the three LAMS values; a new campaign has Sent, Responded and Applied statuses
- [ ] **AC-18 (all but the report):** a borrower whose Pre_Approved__c becomes true joins the active top-up campaign once, as Sent. An application they submit carries that campaign in Campaign__c, and their member status becomes Applied
- [ ] Converting a lead that belongs to a campaign sets the application's Campaign__c; Web-to-Lead and callback leads can carry a campaign as Campaign Members
- [ ] Officers can choose Campaign__c on the staff path of New Loan Application; portal borrowers can't see it
- [ ] Campaign bookkeeping failures never block a submission or a Contact save (tested)
- [ ] 200 borrowers flagged in one update → 200 memberships
- [ ] `CampaignAutomationTest` and the updated test classes pass; coverage ≥ 90% for every Apex class changed here
- [ ] Metadata in `force-app/`; manual steps (Marketing User, Applied status fallback if used) in the README
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-88, BR-89; §9 AC-18; §10.12 Campaign types and member statuses, Loan_Application__c.Campaign__c, campaign influence note; §11 Campaign OWD, LAMS_Policy_Admin and Marketing User; §13.2 Application Submitted, New Loan Application; §13.6 Pre-approved Campaign Membership, Campaign Applied; §17 Data Cloud activation (Pre_Approved__c); Appendix C (C5)
