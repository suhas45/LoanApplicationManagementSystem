# LAMS-088 · Data Cloud: ingest, map, identity resolution

**Milestone:** [M12 – AI and Data Cloud](README.md) · **Size:** L (5–10h) · **Delivers:** BR-78

**Depends on:** LAMS-002 (Data Cloud provisioned, limits noted), LAMS-008 (Contact PAN__c), LAMS-016 (demo borrowers), M08 done (loans, instalments and payments exist)

## Goal

Data Cloud ingests borrowers, applications, loans, instalments and payments from the org. It maps them to the data model and resolves them into one unified borrower profile, with PAN as the party identifier. LAMS-089 builds the repayment score, pre-approved flag and early-risk alert on this profile (BR-78).

## Build

Data Cloud (renamed Data 360 in recent releases) is set up in the org, not deployed from source (§19). Screens and limits vary by release and edition; the tables give the intent and key settings, so verify each one in your org. Data_Cloud_Enabled__c (§12, default false) does not stop Data Cloud itself. It gates the Salesforce-side consumers built in LAMS-089 (the alert flow and agent grounding).

**Setup prerequisites**

| Item | Value |
| --- | --- |
| Data Cloud | Provisioned in the Developer Edition (Data Cloud Setup → Get Started) |
| Admin access | Data Cloud Admin (or Architect) permission set for your admin user |
| Connector | Salesforce CRM connector to the home org (created automatically, or add it) |
| Data space | `default` |

**Data streams** (Salesforce CRM, one per object; refresh as offered by the connector)

| Object | Category | Primary key | Event time (Engagement only) | Notes |
| --- | --- | --- | --- | --- |
| Contact | Profile | Id | – | Add DLO formula fields `pan_type__c = "PAN"` and `pan_party_id__c = Id + "_PAN"` (proposed) for Party Identification |
| Loan_Application__c | Other | Id | – | |
| Loan__c | Other | Id | – | |
| EMI_Instalment__c | Other | Id | – | Rows change status, so not Engagement |
| Payment__c | Engagement | Id | Payment_Date__c | Payments are not edited (BR-45); only status changes |

Ingest only fields you map. Leave out PAN__c on every object except Contact, and leave out Payout_Account__c entirely (NFR-06).

**DMO mappings**

| Source (DLO) | DMO | Field mapping |
| --- | --- | --- |
| Contact | Individual | Id → Individual Id; FirstName → First Name; LastName → Last Name; Birthdate → Birth Date |
| Contact | Contact Point Email | Id → Contact Point Email Id; Id → Party; Email → Email Address |
| Contact | Contact Point Phone | Id → Contact Point Phone Id; Id → Party; MobilePhone (or Phone) → Telephone Number |
| Contact | Party Identification | pan_party_id__c → Party Identification Id; Id → Party; PAN__c → Identification Number; pan_type__c → Party Identification Type and Identification Name |
| Loan__c | **LAMS Loan** (custom, `LAMS_Loan__dlm`; name proposed) | Id → Loan Id (PK); Name → Loan Number; Borrower__c → Borrower Id (relationship to Individual.Individual Id); Loan_Product__c → Product Id; Principal__c; Status__c; Disbursement_Date__c; Days_Past_Due__c; Assigned_Officer__c → Assigned Officer Id |
| EMI_Instalment__c | **LAMS EMI Instalment** (custom, `LAMS_EMI_Instalment__dlm`, proposed) | Id → Instalment Id (PK); Loan__c → Loan Id (relationship to LAMS Loan); Instalment_No__c; Due_Date__c; EMI_Amount__c; Late_Fee__c; Amount_Paid__c; Paid_Date__c; Status__c |
| Payment__c | **LAMS Payment** (custom, `LAMS_Payment__dlm`; name proposed) | Id → Payment Id (PK); Loan__c → Loan Id (relationship to LAMS Loan); Amount__c; Payment_Date__c; Mode__c; Status__c |
| Loan_Application__c | **LAMS Loan Application** (custom, `LAMS_Loan_Application__dlm`, proposed) | Id → Application Id (PK); Name; Borrower__c → Borrower Id (relationship to Individual); Loan_Product__c; Status__c; Amount__c; Submitted_Date__c |

The BRD lists custom DMOs only for Loan and Payment. The instalment DMO is needed for Avg_Days_Late and "no overdue in 12 months" (LAMS-089), and the application DMO makes the profile span applications as BR-78 asks. Both are marked proposed.

Map base fields, not formulas. Formula fields such as Overdue_Bucket__c or Balance_Due__c can change without the record changing, so the ingested value goes stale. Derive them in calculated insights instead.

**Identity resolution ruleset** `LAMS Borrowers` (proposed), on Individual

| # | Match rule | Criteria |
| --- | --- | --- |
| 1 | PAN (party identifier) | Party Identification: Identification Number **Exact** + Party Identification Type = PAN **Exact** |
| 2 | Email + name (proposed tightening) | Email Address **Exact Normalized** + Last Name **Exact** + First Name **Fuzzy** |
| 3 | Phone + name (proposed tightening) | Telephone Number **Exact Normalized** + Last Name **Exact** |

Rules 2 and 3 add a name match so two different PANs that share a family email or phone are not merged. PAN is unique in the org (BR-02), so that would be a wrong merge.

| Reconciliation | Rule |
| --- | --- |
| First Name, Last Name, Birth Date | Last Updated |
| Email, Phone | Last Updated |
| Schedule | Daily (proposed); run it manually for the demo. Developer Edition may cap runs per day, so check the limit |

## Steps

1. Confirm Data Cloud is provisioned and assign yourself the admin permission set. Note the edition limits (data rows, ruleset runs, credits) in [ORG_NOTES.md](../M01-org-and-repo/ORG_NOTES.md).
2. Create the five CRM data streams with the categories above, and add the two Contact formula fields. Wait for the first ingestion; check record counts against SOQL counts in the org.
3. Create the four custom DMOs and map all streams as in the table. Set the relationships: LAMS Loan → Individual, EMI Instalment → LAMS Loan, Payment → LAMS Loan, Application → Individual.
4. Create the `LAMS Borrowers` ruleset with the three match rules and the reconciliation rules; run it.
5. Validate in Data Explorer or Query Editor:
   `SELECT COUNT(*) FROM UnifiedIndividual__dlm` (expect the number of Contacts with a PAN, since there is one source and PAN is unique). Open one demo borrower in Profile Explorer and check that the loans and payments are linked.
6. Record the manual setup (streams, mappings, ruleset, screenshots) in `docs/DATA_CLOUD_SETUP.md` (proposed) for the README (LAMS-092). Commit it: `docs(data-cloud): ingest, mappings and identity resolution setup [LAMS-088]`. If your release supports data kits, you may also package the streams and mappings and retrieve the kit; otherwise the doc is the source of truth.

## Learn

- **DLO → DMO:** data lands as-is in Data Lake Objects; mapping to Data Model Objects gives it a standard shape that segments, insights and identity resolution understand.
- **Party identifier:** a business key like PAN goes in the Party Identification DMO. An exact match on it is the strongest rule; email and phone rules catch records without a PAN but risk wrong merges.
- **Consolidation rate:** with one CRM source and a unique PAN, unified profiles ≈ contacts. That is expected here. Identity resolution adds real value when a second source (for example legacy servicing) arrives.
- **Category matters:** Engagement streams need an immutable event time and suit append-only data (payments). Rows that change (instalment status) go in Other.

## Done when

- [ ] Five data streams ingest, and DLO record counts match the org's counts
- [ ] Contact is mapped to Individual, Contact Point Email, Contact Point Phone and Party Identification (PAN), and the four custom DMOs are mapped with their relationships
- [ ] The `LAMS Borrowers` ruleset runs; Unified Individual count equals the number of Contacts with a PAN
- [ ] Profile Explorer shows a demo borrower with their applications, loans, instalments and payments
- [ ] Payout_Account__c is not ingested anywhere, and PAN__c only on Contact
- [ ] Manual setup documented with screenshots for LAMS-092
- [ ] Meets the [Definition of Done](../README.md#definition-of-done)

## References

- [BRD](../../BRD/LAMS_BRD.md): §6.15 BR-78, §17 Data Cloud table (Ingest, Map, Identity resolution), §10.1 PAN__c (Data Cloud match key), BR-02, §12 Data_Cloud_Enabled__c, §8 C1, C4, §19 "Not in source", NFR-06
