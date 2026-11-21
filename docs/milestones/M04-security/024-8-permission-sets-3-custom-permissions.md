# LAMS-024 · 8 permission sets + 3 custom permissions

**Milestone:** [M04 – Security](README.md) · **Size:** L (5–10h) · **Delivers:** §11

**Depends on:** LAMS-023; M02 done (all objects and fields exist)

## Goal

Eight permission sets grant each job exactly the object, field and system access it needs, and three custom permissions gate override, waiver and settings authority. Access is least-privilege and auditable (BR-70 – BR-74, NFR-06). Later items only add class, flow and tab access to these sets. They never invent new ones.

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
| Case | – | R E (p, disputes) | – | R E (p) | R C | – |
| Contact, Account | profile | profile | – | profile | profile | R C E (p, partner borrowers by PAN) |

`LAMS_Reports` and `LAMS_Agentforce_User` grant no object access.

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
| LAMS_Credit | none | – | LAMS_Override_Credit_Check, LAMS_Waive_Late_Fee | Tabs: Applications, Products, Loans, Cases. App: LAMS |
| LAMS_Policy_Admin | none | – | LAMS_Manage_Settings | Apex class `LamsSettingsController` and the LAMS Settings tab (added in LAMS-030). Tab: Integration Logs |
| LAMS_Operations | none | **View Encrypted Data** | – | Tabs: Applications, Loans, Cases. App: LAMS |
| LAMS_Borrower_Portal | Customer Community Login | – | – | Assigned directly to portal users |
| LAMS_Reports | none | Run Reports, Create and Customize Reports (p) | – | Not Export Reports (proposed, privacy) |
| LAMS_Agentforce_User | none | – | – | Created now as a shell. Agent access and agent-action Apex classes are added in LAMS-086 |
| LAMS_Integration | none | API Enabled, API Only User | – | Apex classes `LoanApplicationApi`, `PaymentCallbackApi`, `LoanStatusWebService` (added in M09). The user also needs the *Salesforce API Integration* permission set licence (LAMS-068) |

Every set gets a Description that names its BR IDs, for example "Loan Officer capture and document verification (BR-01, BR-17, BR-18)".

## Steps

1. Create the 3 custom permissions (Setup → Custom Permissions).
2. Create the 8 permission sets. For each one, set object settings, field permissions, system permissions and custom permissions as in the tables. Use **Object Settings** in the permission set UI to set object and field access on one page.
3. Retrieve with the objects in the same request, so the field permissions come back:
   `sf project retrieve start --metadata PermissionSet:LAMS_Loan_Officer PermissionSet:LAMS_Credit PermissionSet:LAMS_Policy_Admin PermissionSet:LAMS_Operations PermissionSet:LAMS_Borrower_Portal PermissionSet:LAMS_Reports PermissionSet:LAMS_Agentforce_User PermissionSet:LAMS_Integration CustomPermission:LAMS_Override_Credit_Check CustomPermission:LAMS_Waive_Late_Fee CustomPermission:LAMS_Manage_Settings`
4. Review each `.permissionset-meta.xml` against the tables. Search for `<editable>true</editable>` on `PAN__c`, `Monthly_Income__c` and `Credit_Score__c` and confirm only the expected sets have it.
5. Deploy to prove it is clean: `sf project deploy start --source-dir force-app/main/default/permissionsets force-app/main/default/customPermissions --dry-run`.
6. Commit: `feat(security): 8 LAMS permission sets and 3 custom permissions [LAMS-024]`.

## Learn

- **Permission sets only add access.** Removing access needs a muting permission set inside a group (LAMS-025), or simply not granting it.
- **Object access vs record access:** `R E` on Loan_Product__c lets a user edit products only on records they can reach. Loan_Product__c is *Public Read Only*, so the Credit Head also needs record-level write (the sharing rule in LAMS-026), or the Edit button never appears.
- **Licence-bound sets:** a permission set with License *Customer Community Login* can be assigned only to portal users, and the UI shows only permissions that licence allows. A set with no licence can be assigned to anyone whose licence supports what it grants.
- **FLS gotchas:** universally required fields and master-detail fields don't appear in field permissions (they are always editable). Formula and roll-up fields can only be Read.

## Done when

- [ ] 3 custom permissions and 8 permission sets exist with the API names above and are in `force-app/` (`customPermissions/`, `permissionsets/`)
- [ ] Only LAMS_Credit holds LAMS_Override_Credit_Check and LAMS_Waive_Late_Fee; only LAMS_Policy_Admin holds LAMS_Manage_Settings
- [ ] Only LAMS_Operations has View Encrypted Data; only LAMS_Policy_Admin has View All on Integration_Log__c; only LAMS_Integration has View All on Loan__c
- [ ] LAMS_Operations has no access to Contact.PAN__c, Contact.Monthly_Income__c or Loan_Application__c.Credit_Score__c (groundwork for AC-14)
- [ ] `sf project deploy start --dry-run` of the permission sets succeeds
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Permission sets, Custom permissions, Editing settings, Field-level security; §13.2 Override Credit Score and Waive Late Fee flows; §14 LamsSettingsController; appendix #17, #18; BR-15, BR-18, BR-51, BR-70 – BR-74, NFR-06
