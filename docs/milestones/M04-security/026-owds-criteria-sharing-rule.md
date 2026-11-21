# LAMS-026 · OWDs + criteria sharing rule

**Milestone:** [M04 – Security](README.md) · **Size:** S (≤ 2h) · **Delivers:** BR-70

**Depends on:** LAMS-022; M02 done (including LAMS-094, Account record types)

## Goal

Record access starts closed and opens only on purpose. Private org-wide defaults plus the role hierarchy give Loan Officers their own applications, Credit Managers their team's and the Credit Head everything. One criteria sharing rule gives Operations read-only access to approved applications (BR-70).

## Build

**Org-wide defaults** (internal / external):

| Object | Internal | External | Note |
| --- | --- | --- | --- |
| Account | Private | Private | Individual Borrower and Business Borrower Accounts, one per borrower |
| Contact | Controlled by Parent | Controlled by Parent | **Changed v2.2** (design choice). Every borrower Contact follows its own Account (individual or business), so one owner and one share cover both; the portal sharing set's Account row then covers the Contact too (LAMS-077) |
| Lead | Private | Private (proposed) | **New v2.2.** Opened by the lead queues and assignment rule (LAMS-096) |
| Campaign | Public Read Only | Private (proposed; portal users never see campaigns) | **New v2.2.** Every officer can read campaigns; only LAMS_Policy_Admin users with Marketing User edit them (LAMS-024) |
| Loan_Product__c | Public Read Only | Public Read Only (proposed: borrowers pick a product in the portal) | |
| Loan_Application__c | Private | Private | |
| Loan__c | Private | Private | Opened by Apex managed sharing (LAMS-054) |
| Case | Private | Private | Opened by assignment rules (LAMS-078) and the sharing set (LAMS-077) |
| Integration_Log__c | Private | Private | Credit Head and Admin read all through View All (LAMS-024) |
| Product_Document__c, Application_Document__c, EMI_Instalment__c, Payment__c | Controlled by Parent | Controlled by Parent | Master-detail children |

Check that the Payment__c master-detail field has **Sharing Setting = Read Only** (set in LAMS-013), so the Integration User and Operations can create payments with read access to the loan.

Keep **Grant Access Using Hierarchies** ticked on every custom object.

**Criteria sharing rule on Loan_Application__c**

| Property | Value |
| --- | --- |
| Label / name | Approved Applications to Operations / `Approved_Applications_to_Operations` (proposed) |
| Rule type | Based on criteria |
| Criteria | `Status__c` equals `Approved, Offer Accepted` |
| Share with | Role: **Operations Officer** (role only, not "and subordinates") |
| Access | Read Only |

**Owner-based sharing rule on Loan_Product__c (proposed, needed for BR-74)**

| Property | Value |
| --- | --- |
| Label / name | Products Editable by Credit Head / `Products_Editable_by_Credit_Head` |
| Records owned by | Public group *All Internal Users* |
| Share with | Role: **Credit Head** |
| Access | Read/Write |

Without this rule, the Credit Head has Edit on the object but only read access to products owned by the admin, so the products stay read-only. Record the rule in the milestone Parking lot so the BRD can be updated.

## Steps

1. Setup → Sharing Settings → Edit. Set each OWD from the table and save. Wait for the recalculation email.
2. Sharing Settings → Loan Application Sharing Rules → New, using the first table.
3. Loan Product Sharing Rules → New, using the second table.
4. Retrieve the OWDs (they live on the objects) and the rules:
   `sf project retrieve start --metadata CustomObject:Loan_Application__c CustomObject:Loan__c CustomObject:Loan_Product__c CustomObject:Integration_Log__c CustomObject:Account CustomObject:Contact CustomObject:Lead CustomObject:Campaign CustomObject:Case SharingRules:Loan_Application__c SharingRules:Loan_Product__c`
5. Check that `<sharingModel>` and `<externalSharingModel>` in each `.object-meta.xml` match, and that `sharingRules/Loan_Application__c.sharingRules-meta.xml` has the criteria rule.
6. Commit: `feat(security): private OWDs and Operations criteria sharing rule [LAMS-026]`.

## Learn

- **OWD is the floor; everything else only opens up.** Role hierarchy, sharing rules, Apex sharing and sharing sets add access. Nothing can take away access the OWD gives.
- **External OWD** applies to portal and community users. It can't be more open than the internal OWD.
- **Criteria rules re-evaluate on every save.** When an application leaves *Approved* / *Offer Accepted* (for example to Withdrawn), Operations loses access automatically.
- Changing an OWD or a sharing rule starts a background recalculation. Large data volumes can take a long time, so set OWDs before loading real data.
- **Controlled by Parent on Contact** means a Contact has no sharing of its own: whoever can see the Account sees its Contacts. Because every borrower has their own Account, giving access to the Account gives access to exactly that borrower's Contact.
- Standard objects such as Lead and Campaign always grant access through the role hierarchy, so the Credit Head sees every Loan Officer's leads without a rule.

## Done when

- [ ] Sharing Settings shows the OWDs in the table, internal and external (Contact Controlled by Parent, Lead Private, Campaign Public Read Only)
- [ ] Logged in as an Operations Officer, an application in Draft is not visible, and the same application set to Approved appears Read Only. Re-check this once the LAMS-029 users exist
- [ ] The Credit Head can edit a Loan Product; a Credit Manager can't (also checks the LAMS-025 muting set)
- [ ] Object files and `sharingRules/` files are in `force-app/` and deploy cleanly
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §11 Org-wide defaults, Role hierarchy, Sharing; §10.1 borrower Accounts; appendix #18, #19; Appendix C (C2); BR-59, BR-70, BR-74, BR-84
