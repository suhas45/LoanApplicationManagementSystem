# LAMS-098 · LeadTrigger + LeadConversionService (Draft application on convert) + tests

**Milestone:** [M14 – Sales: leads and campaigns](README.md) · **Size:** L (5–10h) · **Delivers:** BR-87, AC-17

**Depends on:** LAMS-095 (Lead fields incl. Borrower_Type__c, Converted status, field mapping, *Require Validation for Converted Leads*, TestDataFactory lead helpers), LAMS-096 (queues and assignment rule, for the AC-17 owner), LAMS-094 (Account record types `Individual_Borrower` / `Business_Borrower`), LAMS-008 (unique Contact.PAN__c), LAMS-009 (Loan_Application__c, its 4 record types, Channel__c, Status__c), LAMS-031 (amount and tenure rules on the application), LAMS-033 (TestDataFactory), LAMS-035 (Draft shape and *Resume Application*), LAMS-023 / LAMS-024 (Account record-type defaults, Convert Leads and Lead access in `LAMS_Sales_Access`, assigned directly to Priya Sharma, LAMS-029)

## Goal

Converting a Qualified lead creates or reuses the borrower and creates a Draft application with the lead's product, amount and tenure. No Opportunity is created (BR-87, C4).

- An individual lead becomes an **Individual Borrower Account named after the person, with one Contact**.
- A business lead becomes a **Business Borrower Account with the lead as director Contact**.
- A lead whose PAN already belongs to a borrower is converted **into that existing Contact**.

The code is bulk-safe at 200 leads (NFR-01) and idempotent (NFR-05). This item completes the conversion half of **AC-17**: the callback → Individual Borrower Account + Contact → Draft Home application for ₹40 lakh with the requested tenure, and no opportunity. The callback half is LAMS-097. The lead's most recent campaign is found here; LAMS-099 writes it to `Campaign__c`, because that field is created there (BR-88).

## Build

**New field `Loan_Application__c.Source_Lead_Id__c`** (proposed): Text(18), Unique (case-sensitive), External ID. It holds the converted lead's Id and is the idempotency key, the same pattern as `Loan__c.Application_Key__c`. Read-only on the application layouts; Read FLS for LAMS_Sales_Access and LAMS_Credit. LAMS-100 also counts lead-sourced applications with it.

**Trigger `LeadTrigger`**: `trigger LeadTrigger on Lead (after update)`, body `LeadTriggerHandler.afterUpdate(Trigger.newMap, Trigger.oldMap);`. It is the only trigger on Lead (NFR-09). It fires on conversion only because *Require Validation for Converted Leads* is on (LAMS-095).

**Class `LeadTriggerHandler`**: `public with sharing class`. Its single method, `public static void afterUpdate(Map<Id, Lead> newMap, Map<Id, Lead> oldMap)`, picks leads where `IsConverted` went **false → true** and passes them, with `oldMap`, to the service. No other logic.

**Class `LeadConversionService`**: `public without sharing class`. Add a class comment explaining why. The platform has already checked the user's right to convert the lead. The service must still find an existing borrower by PAN and an existing application by Source_Lead_Id__c whoever owns them: Accounts are Private, and a missed match would create a second borrower or a second application. It writes only the new Account, the new Draft application and nothing else.

```apex
public static void createDraftApplications(List<Lead> convertedLeads, Map<Id, Lead> oldMap); // from the trigger
public static List<Database.LeadConvertResult> convert(Set<Id> leadIds);                    // programmatic conversion
@InvocableMethod(label='Convert Lead to Draft Application' category='LAMS')
public static List<ConvertResult> convertFromFlow(List<Id> leadIds);                        // quick-action flow
public class ConvertResult { @InvocableVariable public Id applicationId; @InvocableVariable public String errorMessage; }
@TestVisible static Map<Id, Id> latestCampaignByLead(Set<Id> leadIds);                      // lead Id → Campaign Id
```

**`createDraftApplications`**: one pass, 4 queries at most, whatever the number of leads

| # | Step | On failure |
| --- | --- | --- |
| 1 | `oldMap.get(l.Id).Status` must be `Qualified` (BR-87 "a qualified lead") | `l.addError(System.Label.LAMS_Lead_Convert_Not_Qualified)` |
| 2 | Loan_Product__c, Requested_Amount__c, Requested_Tenure__c not blank | `addError(LAMS_Lead_Convert_Missing_Details)` |
| 3 | Query products `SELECT Id, Active__c, Record_Type_Name__c FROM Loan_Product__c WHERE Id IN :ids`; the product must be active | `addError(LAMS_Lead_Convert_Product_Inactive)` |
| 4 | Query `SELECT Id, RecordType.DeveloperName FROM Account WHERE Id IN :convertedAccountIds`. The record type must match Borrower_Type__c: Individual → `Individual_Borrower`, Business → `Business_Borrower` (two constants in the class) | `addError(LAMS_Lead_Convert_Wrong_Account_Type)`. This catches the standard *Convert* button when it puts a business lead into the user's default Individual Borrower record type, or when the officer picks the wrong existing account |
| 5 | Query `SELECT Source_Lead_Id__c FROM Loan_Application__c WHERE Source_Lead_Id__c IN :leadIdStrings`; skip leads that already have one | Skip silently (idempotent) |
| 6 | Application record type: `Schema.SObjectType.Loan_Application__c.getRecordTypeInfosByDeveloperName().get(product.Record_Type_Name__c)` | `addError(LAMS_Error_Generic)` and a `LoggingLevel.ERROR` debug naming the product (configuration fault) |
| 7 | `latestCampaignByLead(ids)`: built and tested now, assigned in LAMS-099 | – |
| 8 | Build one application per lead (table below); one `Database.insert(apps, false)` | For each failed `SaveResult`, `addError` on its lead with the first error message (for example the LAMS-031 amount-range text). The lead's whole conversion rolls back, so a borrower is never left without the application |

| Loan_Application__c field | Value |
| --- | --- |
| Borrower__c | `lead.ConvertedContactId` |
| Loan_Product__c | `lead.Loan_Product__c` |
| Amount__c | `lead.Requested_Amount__c` |
| Tenure__c | `lead.Requested_Tenure__c` |
| RecordTypeId | From step 6 (Home for HL, and so on) |
| Channel__c | `Branch` (§14) |
| Status__c | `Draft` |
| Last_Activity_Date__c | `System.now()` (drives 30-day expiry, LAMS-064) |
| OwnerId | `lead.OwnerId` when it is a User (`005` prefix), else `UserInfo.getUserId()` |
| Source_Lead_Id__c | `lead.Id` |
| Campaign__c | Added in LAMS-099: `campaignByLead.get(lead.Id)` |

Purpose__c and the product-specific fields stay blank. The officer completes them with *Resume Application* (LAMS-035) before submitting.

**`latestCampaignByLead`**: `SELECT LeadId, CampaignId FROM CampaignMember WHERE LeadId IN :leadIds ORDER BY CreatedDate DESC`. The first row per lead wins. Conversion keeps the CampaignMember rows and fills in their ContactId, so the query still works after the lead converts.

**`convert(leadIds)`**: the path the officer uses, through the quick action

| # | Step |
| --- | --- |
| 1 | `SELECT Id, Status, OwnerId, PAN__c, Company, City, Borrower_Type__c FROM Lead WHERE Id IN :leadIds AND IsConverted = false WITH USER_MODE`. Only leads the user can see are converted |
| 2 | Converted status: `SELECT MasterLabel FROM LeadStatus WHERE IsConverted = true LIMIT 1` |
| 3 | Existing borrowers: `SELECT Id, AccountId, PAN__c FROM Contact WHERE PAN__c IN :pans AND AccountId != null` → map by PAN |
| 4 | For leads **without** a PAN match, pre-create the Account so it gets the right record type: `Name = lead.Company`, `RecordTypeId` from Borrower_Type__c, `OwnerId` = new owner (below), `BillingCity = lead.City`. One insert, with `DuplicateRuleHeader.allowSave = true`, because the standard Account rule matches on name and two different people can share one |
| 5 | One `Database.LeadConvert` per lead: `setLeadId`, `setConvertedStatus(step 2)`, `setDoNotCreateOpportunity(true)`, `setSendNotificationEmail(false)`, `setAccountId` (existing borrower's AccountId, or the pre-created Account), `setContactId(existing.Id)` on a PAN match. When the lead is owned by a queue: `setOwnerId(UserInfo.getUserId())`. Converted records can only be owned by users |
| 6 | Convert in chunks of **100** (the per-call maximum): `Database.convertLead(chunk, false, AccessLevel.USER_MODE)`, so the user's own Convert Leads and object permissions apply |
| 7 | Delete the pre-created Accounts whose `LeadConvertResult` failed (no orphan borrowers); return all results |

A pre-created Individual Borrower Account gets exactly one Contact: the one conversion creates. That keeps the one-Account-per-borrower convention (LAMS-094).

**`convertFromFlow`** calls `convert`, then reads `Loan_Application__c` by `Source_Lead_Id__c` to return the application Id. On failure it returns the first error message.

**Flow `Convert_Lead_to_Application`** (Screen Flow; label *Convert to Application*; run in user context). Quick action *Convert to Application* on Lead, on `LAMS_Lead_Record_Page` with Dynamic Actions visibility `Status = Qualified`.

| # | Element | Details |
| --- | --- | --- |
| 1 | Screen *Confirm* | Shows Company, Borrower Type, Product, Requested Amount and Tenure, PAN; text label `LAMS_Lead_Convert_Confirm` |
| 2 | Action | `Convert Lead to Draft Application` with `{!recordId}` |
| 3 | Decision | errorMessage blank? |
| 4 | Screen *Done* / *Error* | `LAMS_Lead_Convert_Done` with a link `/lightning/r/Loan_Application__c/{!applicationId}/view`, or the error message |

Remove the standard **Convert** button from the LAMS Lead Layout (proposed). It can't reuse a borrower by PAN, and it uses the default record type. It still works from the Path's last step. If it is used, the trigger still creates the application, and step 4 stops a business lead from landing in an Individual Borrower Account.

**Custom labels** (category `LAMS Sales`; Hindi drafts)

| Label | English | Hindi (draft) |
| --- | --- | --- |
| LAMS_Lead_Convert_Not_Qualified | Only a Qualified lead can be converted. Complete the loan details and mark it Qualified first. | केवल Qualified लीड को ही बदला जा सकता है। पहले ऋण विवरण पूरा करें और इसे Qualified चिह्नित करें। |
| LAMS_Lead_Convert_Missing_Details | The lead needs a loan product, amount and tenure before it can be converted. | बदलने से पहले लीड में ऋण उत्पाद, राशि और अवधि होनी चाहिए। |
| LAMS_Lead_Convert_Product_Inactive | The lead's loan product is no longer offered. Choose an active product. | लीड का ऋण उत्पाद अब उपलब्ध नहीं है। कोई सक्रिय उत्पाद चुनें। |
| LAMS_Lead_Convert_Wrong_Account_Type | The borrower account type doesn't match the lead's borrower type. Use Convert to Application, or choose a matching account. | उधारकर्ता खाते का प्रकार लीड के उधारकर्ता प्रकार से मेल नहीं खाता। Convert to Application का उपयोग करें या मेल खाने वाला खाता चुनें। |
| LAMS_Lead_Convert_Confirm | Convert this lead into a borrower and a Draft application? No opportunity is created. | इस लीड को उधारकर्ता और ड्राफ़्ट आवेदन में बदलें? कोई अवसर (opportunity) नहीं बनाया जाएगा। |
| LAMS_Lead_Convert_Done | Draft application created. Open it to complete the details and submit. | ड्राफ़्ट आवेदन बन गया। विवरण पूरा करने और जमा करने के लिए इसे खोलें। |

**Access:** Apex class `LeadConversionService` and flow `Convert_Lead_to_Application` go on **LAMS_Sales_Access** (BRD v2.3, D6), not on LAMS_Loan_Officer: only full-licence users who hold Lead access can convert.

**Feature toggle:** none. BR-79 lists no toggle for leads, so the toggle on/off rule of the Definition of Done doesn't apply here. Say so in the test class header.

**Tests `LeadConversionServiceTest`.** Products from `TestDataFactory.createProduct`, leads from `newLead` / `insertLeads` (LAMS-095). Use the existing Loan Officer from `TestDataFactory.loanOfficer()`: the org has no spare Salesforce licence for a new test user.

| Test | Arrange | Assert |
| --- | --- | --- |
| `ac17_homeLoanLeadBecomesIndividualBorrowerAndDraft` | HL lead, Company "Rohit Kulkarni", Individual, City Pune, ₹40,00,000, 240 months, inserted with assignment (owner Leads_Secured); Status Qualified. `System.runAs(loanOfficer)`: `convert(...)` | Result success, `getOpportunityId()` null, `[SELECT COUNT() FROM Opportunity] = 0`. Account Name "Rohit Kulkarni", record type Individual_Borrower, exactly 1 Contact. One application: Borrower__c = that Contact, record type Home, Amount 4000000, Tenure 240, Status Draft, Channel Branch, Source_Lead_Id__c = lead Id, owner = the officer (the lead was queue-owned) |
| `businessLeadBecomesBusinessBorrower` | BL lead, Borrower Type Business, Company "Iyer Traders" | Account record type Business_Borrower; Contact under it is Borrower__c; application record type Business |
| `existingBorrowerReusedByPan` | `createBorrower('AAAPS1001A')`; Qualified lead with that PAN | Account and Contact counts unchanged; `getContactId()` = existing Contact; Borrower__c = existing Contact |
| `standardConvertAlsoCreatesApplication` | Plain `Database.LeadConvert` with only lead, status and DoNotCreateOpportunity (what the button does), individual lead, admin user (default Individual Borrower) | Application created by the trigger |
| `standardConvertOfBusinessLeadRefused` | Same for a Business lead | Conversion fails with LAMS_Lead_Convert_Wrong_Account_Type; lead still unconverted |
| `notQualifiedRefused` | Lead in Contacted | Fails with LAMS_Lead_Convert_Not_Qualified; no Account (the pre-created one was deleted), no application |
| `applicationErrorRollsBack` | Qualified HL lead; then raise the product's Min_Amount__c above the requested amount | Fails with the LAMS_VR_Amount_Out_Of_Range text; lead unconverted; no Account left |
| `inactiveProductRefused` | Product set inactive after qualifying | LAMS_Lead_Convert_Product_Inactive |
| `idempotent` | Convert, re-query the lead, call `createDraftApplications` again | Still exactly 1 application |
| `bulk200` | 200 Qualified PL leads (unique PAN and mobile) | 200 successes from 2 `convertLead` calls; 200 Accounts, 200 Contacts, 200 Draft applications; 0 opportunities; no limit errors |
| `latestCampaignWins` | Lead in two campaigns; `Test.setCreatedDate` makes one newer | Map returns the newer Campaign Id; a lead with no membership is absent |
| `flowActionReturnsApplicationId` | `convertFromFlow` with one good and one Contacted lead | First result has applicationId; second has the error message |

## Steps

1. Confirm Lead Settings from LAMS-095: *Require Validation for Converted Leads* on, opportunity section hidden.
2. Create `Source_Lead_Id__c` and its FLS; create the labels with Hindi.
3. Generate the files:
   `sf apex generate class --name LeadConversionService --output-dir force-app/main/default/classes` (likewise `LeadTriggerHandler`, `LeadConversionServiceTest`) and
   `sf apex generate trigger --name LeadTrigger --sobject Lead --event "after update" --output-dir force-app/main/default/triggers`.
4. Write the service, handler, trigger and tests to the spec.
5. Deploy: `sf project deploy start --source-dir force-app/main/default --target-org Lams`.
6. Run: `sf apex run test --class-names LeadConversionServiceTest --code-coverage --result-format human --wait 10 --target-org Lams`.
7. Build the flow and quick action; add the action to the Lead record page; remove the standard Convert button from the layout; grant class and flow access on LAMS_Sales_Access.
8. By hand, as Priya Sharma: create a Pune Home Loan lead (₹40,00,000, 240 months), qualify it and click *Convert to Application*. Check the Account, Contact and Draft application, and that no opportunity exists. Keep this record pair: it is the AC-17 demo and the borrower for LAMS-099.
9. Retrieve: `sf project retrieve start --metadata ApexTrigger:LeadTrigger ApexClass:LeadTriggerHandler ApexClass:LeadConversionService ApexClass:LeadConversionServiceTest ApexClass:TestDataFactory CustomField:Loan_Application__c.Source_Lead_Id__c Flow:Convert_Lead_to_Application QuickAction:Lead.Convert_to_Application "Layout:Lead-LAMS Lead Layout" FlexiPage:LAMS_Lead_Record_Page CustomLabels Translations:hi PermissionSet:LAMS_Sales_Access PermissionSet:LAMS_Credit --target-org Lams`
10. Commit: `feat(apex): LeadConversionService creates borrower and Draft application on convert [LAMS-098]`.

## Learn

- **Lead conversion is a Lead update.** Conversion sets `IsConverted`, `ConvertedAccountId` and `ConvertedContactId` on the Lead and inserts the Account and Contact in the same transaction. Lead update triggers run then only with *Require Validation for Converted Leads* on. Test the false → true change, never `IsConverted` alone. `addError` in the after trigger rolls back that lead's whole conversion.
- **`Database.LeadConvert`:**
  - `setDoNotCreateOpportunity(true)` skips the opportunity.
  - `setAccountId` / `setContactId` merge the lead into existing records.
  - `setOwnerId` is required when a queue owns the lead.
  - At most 100 converts per `convertLead` call.
  - It has no record-type setting, which is why the service pre-creates the Account. The standard button uses the user's default record type.
- **Field mapping stops at Account, Contact and Opportunity.** Anything for a custom object, such as the product, amount and tenure here, is copied in code from the converted Lead.
- **Idempotency with a unique External ID:** `Source_Lead_Id__c` makes a second application for the same lead impossible at the database level. The query in step 5 just avoids the error.

## Done when

- [ ] **AC-17 (conversion part):** a Qualified Pune Home Loan lead for ₹40 lakh, 240 months, converts into an Individual Borrower Account with one Contact and a Draft Home application for ₹40,00,000 and 240 months, Channel Branch, with no opportunity, both in `ac17_…` and by hand
- [ ] A business lead converts into a Business Borrower Account with the director as Borrower__c; a lead whose PAN matches converts into the existing Contact without a new Account
- [ ] Not Qualified, missing details, inactive product, wrong account type and an application validation error each refuse the conversion with their label, leaving no Account or application behind
- [ ] Converting with the standard button also creates the application
- [ ] Re-running the service creates no second application
- [ ] 200 leads convert in one test with 200 applications and no limit errors
- [ ] `latestCampaignByLead` returns the most recent campaign, ready for LAMS-099
- [ ] *Convert to Application* is on the Lead page for Qualified leads and opens the new application
- [ ] Coverage ≥ 90% for LeadConversionService and LeadTriggerHandler; the trigger contains only the handler call
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.17 BR-87, BR-88; §9 AC-17; §10.1 Borrower (record types per LAMS-094, no Person Accounts); §10.3 Loan_Application__c (Channel, Status, record types); §10.12 Lead fields and Campaign__c; §13.2 New Loan Application (record type from Record_Type_Name__c); §14 LeadTrigger + LeadConversionService, Tests; NFR-01, NFR-05, NFR-09, NFR-10; Appendix C (C3, C4)
