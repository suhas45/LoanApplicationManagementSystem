# LAMS-024 · 8 permission sets + 3 custom permissions

**Milestone:** [M04 – Security](README.md) · **Size:** L (5–10h) · **Delivers:** §11

**Depends on:** LAMS-023; M02 done (all objects and fields exist)

## Goal

Ten permission sets grant each job exactly the object, field and system access it needs, and three custom permissions gate override, waiver and settings authority. Access is least-privilege and auditable (BR-70 – BR-74, NFR-06). The title still says 8: BRD v2.3 (§11, Appendix D6) added `LAMS_Sales_Access` and `LAMS_Case_Access`, which hold the Lead, Campaign-read and Case permissions that a Salesforce Platform licence can't take, so the other eight stay assignable to every staff user. Later items only add class, flow and tab access to these sets. They never invent new ones.

## Build

**Custom permissions**

| API name | Label | Description | Checked by |
| --- | --- | --- | --- |
| LAMS_Override_Credit_Check | Override Credit Check | Enter a manual credit score when the bureau is unavailable (BR-15) | Override Credit Score flow (LAMS-044), AC-05 |
| LAMS_Waive_Late_Fee | Waive Late Fee | Waive an instalment's late fee with a reason (BR-51) | Waive Late Fee flow (LAMS-060), EMI validation rule (LAMS-032) |
| LAMS_Manage_Settings | Manage LAMS Settings | Change LAMS_Settings__c org defaults (BR-74) | LamsSettingsController (LAMS-030) |

**Permission sets: object access** (R read · C create · E edit · D delete · VA View All · MA Modify All · – none). "(p)" marks access the BRD doesn't list but the flow of work needs (proposed).

| Object | LAMS_Loan_Officer | LAMS_Credit | LAMS_Policy_Admin | LAMS_Operations | LAMS_Borrower_Portal | LAMS_Integration |
| --- | --- | --- | --- | --- | --- | --- |
| Loan_Application__c | R C E | R E | – | R; E (p) for field verification | R C E (p: E for draft resume, offer response) | R C E |
| Application_Document__c | R C E | R | – | – | R C E (p) | – |
| Loan_Product__c | R | R C E | – | R (p) | R (p) | R (p) |
| Product_Document__c | R | R C E D (p) | – | – | R (p) | – |
| Loan__c | R | R | – | R E | R | R + **VA** |
| EMI_Instalment__c | – | R E (p, waiver) | – | R | R | – |
| Payment__c | – | R | – | R C E (E only for reversal) | R | R C E (E for upsert) |
| Integration_Log__c | – | R (p) | R + **VA** | – | – | R C E (p) |
| Case | – (LAMS_Case_Access) | – (LAMS_Case_Access) | – | – (LAMS_Case_Access) | R C | – |
| Contact, Account | profile | profile | – | profile | profile | R C E (p, partner borrowers by PAN: a new borrower is an Account plus a Contact) |
| Lead (**v2.2**) | – (LAMS_Sales_Access) | – | – | – | – | – |
| Campaign (**v2.2**) | – (LAMS_Sales_Access) | – | R C E | – | – | – |

`LAMS_Reports` and `LAMS_Agentforce_User` grant no object access.

**Licence-bound access sets (v2.3, Appendix D6).** A Salesforce Platform licence has no Lead, Campaign or Case access, and a permission set (or a group containing it) that grants them can't be assigned to a Platform user. So these permissions live in two small sets of their own, **assigned directly to full Salesforce-licence users only and never placed in a permission set group** (LAMS-025):

| Permission set | Object access | System permissions | Also | Assigned to (LAMS-029) |
| --- | --- | --- | --- | --- |
| LAMS_Sales_Access | Lead R C E; Campaign R | **Convert Leads** | Tabs: Leads, Campaigns | Loan Officer 1 |
| LAMS_Case_Access | Case R E (p: disputes for the Credit Head, service requests for Operations) | – | Tab: Cases; Case record type Loan Service Request | Operations Officer 1 and the admin (acting as Credit Head) |

Campaign create/edit stays in LAMS_Policy_Admin; it reaches only the admin, because the LAMS Credit Head group is assigned to no one else.

**Sales access (v2.2, §11).** Lead and Campaign object access is granted now, so the OWDs (LAMS-026) and test users (LAMS-029) can be checked; the Lead custom fields (LAMS-095) and `Loan_Application__c.Campaign__c` (LAMS-099) get their field access in those items, added to LAMS_Sales_Access (Lead fields) and to LAMS_Loan_Officer (`Campaign__c`, proposed: a field on a custom object, so the set stays licence-neutral). Campaign Members need no separate permission: access follows the Campaign and the Lead or Contact. Creating or editing campaigns also needs the **Marketing User** checkbox on the user record (set on the Credit Head in LAMS-029); a permission set cannot grant it.

**Added by the M14 items** (listed here so these sets stay the single place to look):

| Permission set | Added in | Access |
| --- | --- | --- |
| LAMS_Sales_Access | LAMS-095, LAMS-096, LAMS-100 | Lead FLS. Edit: Loan_Product__c, Requested_Amount__c, Requested_Tenure__c, PAN__c, Employment_Type__c, Monthly_Income__c, Preferred_Language__c, Consent__c, Unqualified_Reason__c, Borrower_Type__c. Read: First_Contacted_At__c, Product_Code__c, First_Contact_Overdue__c, Converted_Count__c, Hours_To_First_Contact__c, Web_Product_Code__c (LAMS-097) |
| LAMS_Sales_Access | LAMS-098 | Apex class `LeadConversionService`; flow access `Convert_Lead_to_Application`; Read on `Loan_Application__c.Source_Lead_Id__c` (the UI then also ticks Loan_Application__c Read in this set, which its holders already have through LAMS_Loan_Officer) |
| LAMS_Loan_Officer | LAMS-099 | Edit on `Loan_Application__c.Campaign__c` |
| LAMS_Credit | LAMS-098, LAMS-099 | Read on `Loan_Application__c.Campaign__c` and `Loan_Application__c.Source_Lead_Id__c` |

The admin acts as Credit Head and reads every Lead and Campaign field as System Administrator, so LAMS_Policy_Admin gets no Lead access.

**Licences in the `Lams` org (LAMS-029).** Lead, Campaign and Case exist only for full **Salesforce** licence users: the admin (acting as Credit Head), Loan Officer 1 and Operations Officer 1. The Credit Manager, Loan Officer 2 and Operations Officer 2 have **Salesforce Platform** licences and get only the licence-neutral sets: Loan Officer 2 works no leads, Operations Officer 2 handles loans but no Cases, and the Credit Manager gets no Disputes (they go to the Credit Head queue, LAMS-078).

**Field edit access** (Read on every other field of an object the set can read, except the sensitive fields in LAMS-027):

| Permission set | Edit on |
| --- | --- |
| LAMS_Loan_Officer | Loan_Application__c: Amount__c, Tenure__c, Purpose__c, Channel__c, Status__c, Property_Value__c, Vehicle_Price__c, Dealer_Name__c, GST_Number__c, Annual_Turnover__c, Withdrawal_Reason__c, Last_Activity_Date__c, AI_Summary__c. Application_Document__c: Status__c, Rejection_Reason__c, Verified_By__c, Verified_Date__c. Contact: PAN__c, Monthly_Income__c, Existing_EMI__c, Employment_Type__c, Preferred_Language__c |
| LAMS_Credit | Loan_Application__c: Status__c, Approved_Amount__c, Decision_Comments__c, Rejection_Reason__c, Decision_Date__c, Credit_Score__c, Credit_Score_Source__c, Override_Reason__c, AI_Summary__c. All Loan_Product__c and Product_Document__c fields. EMI_Instalment__c: Late_Fee__c, Late_Fee_Waived__c, Waiver_Reason__c |
| LAMS_Operations | Loan__c: Payout_Account__c, Disbursement_Status__c. Payment__c: Amount__c, Payment_Date__c, Mode__c, Reference__c, Status__c, Reversal_Reason__c (validation rules lock the first four after insert, LAMS-032). Loan_Application__c: Field_Verification_Status__c (p) |
| LAMS_Borrower_Portal | Loan_Application__c: Amount__c, Tenure__c, Purpose__c and the product-specific fields, Withdrawal_Reason__c. **Not** Status__c, decision or eligibility fields (proposed: flows that move status run in system context). Application_Document__c: none (the upload component sets Uploaded through Apex, so a borrower can never set Verified, BR-18) |
| LAMS_Integration | Loan_Application__c: capture fields, External_Reference__c, Partner_Name__c, Channel__c, Status__c. Payment__c: all fields. Integration_Log__c: all fields. Contact: PAN__c, Birthdate, Employment_Type__c, Monthly_Income__c, Existing_EMI__c |

**Other settings**

| Permission set | License | System permissions | Custom permissions | Also |
| --- | --- | --- | --- | --- |
| LAMS_Loan_Officer | none | – | – | Tabs: Applications, Products, Loans. Record types: all 4 application types. App: LAMS |
| LAMS_Credit | none | – | LAMS_Override_Credit_Check, LAMS_Waive_Late_Fee | Tabs: Applications, Products, Loans. App: LAMS |
| LAMS_Policy_Admin | none | – | LAMS_Manage_Settings | Apex class `LamsSettingsController` and the LAMS Settings tab (added in LAMS-030). Tabs: Integration Logs, Campaigns (v2.2) |
| LAMS_Operations | none | **View Encrypted Data** | – | Tabs: Applications, Loans. App: LAMS |
| LAMS_Borrower_Portal | Customer Community Login | – | – | Assigned directly to portal users |
| LAMS_Reports | none | Run Reports, Create and Customize Reports (p) | – | Not Export Reports (proposed, privacy) |
| LAMS_Agentforce_User | none | – | – | Created now as a shell. Agent access and agent-action Apex classes are added in LAMS-086 |
| LAMS_Integration | none | API Enabled, API Only User | – | Apex classes `LoanApplicationApi`, `PaymentCallbackApi`, `LoanStatusWebService` (added in M09). The user also needs the *Salesforce API Integration* permission set licence (LAMS-068) |
| LAMS_Sales_Access | none | **Convert Leads** | – | See the licence-bound table above; assigned directly. Apex class `LeadConversionService` and flow `Convert_Lead_to_Application` are added in LAMS-098 |
| LAMS_Case_Access | none | – | – | See the licence-bound table above; assigned directly |

Every set gets a Description that names its BR IDs, for example "Loan Officer capture and document verification (BR-01, BR-17, BR-18)".

## Steps

1. Create the 3 custom permissions (Setup → Custom Permissions).
2. Create the 10 permission sets. For each one, set object settings, field permissions, system permissions and custom permissions as in the tables. Use **Object Settings** in the permission set UI to set object and field access on one page.
3. Retrieve with the objects in the same request, so the field permissions come back:
   `sf project retrieve start --metadata PermissionSet:LAMS_Loan_Officer PermissionSet:LAMS_Credit PermissionSet:LAMS_Policy_Admin PermissionSet:LAMS_Operations PermissionSet:LAMS_Borrower_Portal PermissionSet:LAMS_Reports PermissionSet:LAMS_Agentforce_User PermissionSet:LAMS_Integration PermissionSet:LAMS_Sales_Access PermissionSet:LAMS_Case_Access CustomPermission:LAMS_Override_Credit_Check CustomPermission:LAMS_Waive_Late_Fee CustomPermission:LAMS_Manage_Settings`
4. Review each `.permissionset-meta.xml` against the tables. Search for `<editable>true</editable>` on `PAN__c`, `Monthly_Income__c` and `Credit_Score__c` and confirm only the expected sets have it.
5. Deploy to prove it is clean: `sf project deploy start --source-dir force-app/main/default/permissionsets force-app/main/default/customPermissions --dry-run`.
6. Commit: `feat(security): 10 LAMS permission sets and 3 custom permissions [LAMS-024]`.

## Learn

- **Permission sets only add access.** Removing access needs a muting permission set inside a group (LAMS-025), or simply not granting it.
- **Object access vs record access:** `R E` on Loan_Product__c lets a user edit products only on records they can reach. Loan_Product__c is *Public Read Only*, so the Credit Head also needs record-level write (the sharing rule in LAMS-026), or the Edit button never appears.
- **Licence-bound sets:** a permission set with License *Customer Community Login* can be assigned only to portal users, and the UI shows only permissions that licence allows. A set with no licence can be assigned to anyone whose licence supports what it grants; a Salesforce Platform licence does not support Lead, Campaign, Case or Opportunity. Keeping those permissions in their own sets is what lets one LAMS_Loan_Officer set serve both licences.
- **FLS gotchas:** universally required fields and master-detail fields don't appear in field permissions (they are always editable). Formula and roll-up fields can only be Read.
- **Convert Leads** needs create/edit on Lead plus create on Account and Contact (the profile gives those). LAMS creates no Opportunity on conversion (BR-87); the profile grants no Opportunity access, so check early in your org that conversion works without it (Lead Settings can hide the opportunity section of the convert screen).

## Done when

- [ ] 3 custom permissions and 10 permission sets exist with the API names above and are in `force-app/` (`customPermissions/`, `permissionsets/`)
- [ ] Only LAMS_Credit holds LAMS_Override_Credit_Check and LAMS_Waive_Late_Fee; only LAMS_Policy_Admin holds LAMS_Manage_Settings
- [ ] Only LAMS_Operations has View Encrypted Data; only LAMS_Policy_Admin has View All on Integration_Log__c; only LAMS_Integration has View All on Loan__c
- [ ] LAMS_Operations has no access to Contact.PAN__c, Contact.Monthly_Income__c or Loan_Application__c.Credit_Score__c (groundwork for AC-14)
- [ ] Only LAMS_Sales_Access has Lead create/edit, Convert Leads and Campaign read; only LAMS_Policy_Admin has Campaign create/edit; only LAMS_Case_Access (and LAMS_Borrower_Portal) has Case access
- [ ] LAMS_Loan_Officer, LAMS_Credit and LAMS_Operations contain no Lead, Campaign or Case permission, so they can be assigned to a Salesforce Platform user
- [ ] `sf project deploy start --dry-run` of the permission sets succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Permission sets, Custom permissions, Editing settings, Field-level security; §13.2 Override Credit Score and Waive Late Fee flows; §14 LamsSettingsController; appendix #17, #18; Appendix C (C3); Appendix D6; BR-15, BR-18, BR-51, BR-70 – BR-74, BR-84, BR-87, BR-88, NFR-06
